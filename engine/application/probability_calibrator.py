"""probability_calibrator.py · v4.2 概率校准层

用途：
对三流派融合后的原始概率进行校准，提升预测准确性。

校准方法：
1. Temperature Scaling（温度缩放）：调整概率分布的"尖锐度"
2. Platt Scaling（Platt 标定）：用 logistic 回归拟合原始概率到真实概率
3. Isotonic Regression（保序回归）：非参数校准，保证单调性

设计原则：
- 在线更新：每次反馈后更新校准参数
- 领域自适应：不同领域（婚姻/事业/健康）用独立校准器
- 降级策略：校准样本不足时，使用全局默认参数

数学原理：
- Temperature Scaling: p_cal = softmax(logits / T)，T>1 使分布平滑，T<1 使分布尖锐
- Platt Scaling: p_cal = 1 / (1 + exp(A * p + B))，A/B 通过历史反馈拟合

依赖：
- numpy（可选，降级为 Python 内置 math）
- cases/*/prediction_feedback.jsonl（校准样本来源）
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CalibrationParams:
    """单个领域的校准参数。"""
    domain: str
    temperature: float = 1.0           # Temperature Scaling 参数
    platt_a: float = 1.0               # Platt Scaling A
    platt_b: float = 0.0               # Platt Scaling B
    sample_count: int = 0              # 校准样本数
    last_updated: str = ""             # 最后更新时间

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "temperature": round(self.temperature, 4),
            "platt_a": round(self.platt_a, 4),
            "platt_b": round(self.platt_b, 4),
            "sample_count": self.sample_count,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CalibrationParams:
        return cls(
            domain=d["domain"],
            temperature=d.get("temperature", 1.0),
            platt_a=d.get("platt_a", 1.0),
            platt_b=d.get("platt_b", 0.0),
            sample_count=d.get("sample_count", 0),
            last_updated=d.get("last_updated", ""),
        )


@dataclass
class ProbabilityCalibrator:
    """v4.2 概率校准器（支持多领域独立校准）。"""
    domain_params: dict[str, CalibrationParams] = field(default_factory=dict)
    global_temperature: float = 1.0    # 全局默认温度（样本不足时使用）
    min_samples_for_calibration: int = 10  # 最少需要 10 个样本才启用校准

    def calibrate(
        self,
        raw_probability: float,
        domain: str,
        *,
        method: str = "temperature",
    ) -> float:
        """对原始概率进行校准。

        Args:
            raw_probability: 原始概率（0-1）
            domain: 领域名称
            method: 校准方法 [temperature, platt, identity]

        Returns:
            校准后的概率（0-1）
        """
        # 边界检查
        raw_probability = max(0.0, min(1.0, raw_probability))

        if method == "identity":
            return raw_probability

        # 获取领域校准参数
        params = self.domain_params.get(domain)

        # 样本不足时，使用全局温度
        if not params or params.sample_count < self.min_samples_for_calibration:
            if method == "temperature":
                return self._temperature_scaling(raw_probability, self.global_temperature)
            else:
                return raw_probability  # 降级为恒等映射

        # 领域专用校准
        if method == "temperature":
            return self._temperature_scaling(raw_probability, params.temperature)
        elif method == "platt":
            return self._platt_scaling(raw_probability, params.platt_a, params.platt_b)
        else:
            return raw_probability

    def _temperature_scaling(self, prob: float, temperature: float) -> float:
        """Temperature Scaling: p_cal = softmax(logit(p) / T)。"""
        if prob <= 0.0 or prob >= 1.0:
            return prob  # 边界情况不校准

        # logit(p) = log(p / (1-p))
        logit = math.log(prob / (1.0 - prob))
        scaled_logit = logit / temperature

        # sigmoid(x) = 1 / (1 + exp(-x))
        calibrated = 1.0 / (1.0 + math.exp(-scaled_logit))
        return max(0.0, min(1.0, calibrated))

    def _platt_scaling(self, prob: float, a: float, b: float) -> float:
        """Platt Scaling: p_cal = 1 / (1 + exp(a * logit(p) + b))。"""
        if prob <= 0.0 or prob >= 1.0:
            return prob

        logit = math.log(prob / (1.0 - prob))
        scaled = a * logit + b

        calibrated = 1.0 / (1.0 + math.exp(-scaled))
        return max(0.0, min(1.0, calibrated))

    def update_from_feedback(
        self,
        domain: str,
        predicted_prob: float,
        actual_outcome: bool,  # True=命中, False=失败
    ) -> None:
        """根据单次反馈更新校准参数（在线学习）。

        简化实现：使用滑动平均更新 temperature。
        完整实现需要积累样本后用 logistic regression 拟合 Platt 参数。
        """
        if domain not in self.domain_params:
            self.domain_params[domain] = CalibrationParams(domain=domain)

        params = self.domain_params[domain]
        params.sample_count += 1

        # 计算校准误差：预测概率 vs 实际结果
        error = predicted_prob - (1.0 if actual_outcome else 0.0)

        # 简化温度更新：如果系统过于自信（error 绝对值大），提高温度使分布平滑
        learning_rate = 0.01
        if abs(error) > 0.3:
            if error > 0:  # 过于自信（预测高但失败）
                params.temperature += learning_rate
            else:  # 过于保守（预测低但成功）
                params.temperature -= learning_rate

        # 限制温度范围 [0.5, 2.0]
        params.temperature = max(0.5, min(2.0, params.temperature))
        params.last_updated = _utc_now()

    def batch_fit_platt(
        self,
        domain: str,
        samples: list[tuple[float, bool]],
    ) -> None:
        """批量拟合 Platt Scaling 参数（需要足够样本）。

        Args:
            domain: 领域
            samples: [(predicted_prob, actual_outcome), ...]

        注意：这里使用简化的最大似然估计。
        完整实现应使用 scipy.optimize 或 sklearn.calibration。
        """
        if len(samples) < self.min_samples_for_calibration:
            return

        if domain not in self.domain_params:
            self.domain_params[domain] = CalibrationParams(domain=domain)

        params = self.domain_params[domain]

        # 简化 Platt Scaling 拟合：用梯度下降最小化交叉熵
        a, b = 1.0, 0.0
        lr = 0.01
        epochs = 100

        for _ in range(epochs):
            grad_a, grad_b = 0.0, 0.0
            for pred_prob, outcome in samples:
                if pred_prob <= 0.0 or pred_prob >= 1.0:
                    continue

                logit = math.log(pred_prob / (1.0 - pred_prob))
                z = a * logit + b
                p_cal = 1.0 / (1.0 + math.exp(-z))

                y = 1.0 if outcome else 0.0
                error = p_cal - y

                # 梯度：∂L/∂a = error * logit, ∂L/∂b = error
                grad_a += error * logit
                grad_b += error

            # 梯度下降
            a -= lr * grad_a / len(samples)
            b -= lr * grad_b / len(samples)

        params.platt_a = max(-5.0, min(5.0, a))  # 限制范围防止过拟合
        params.platt_b = max(-5.0, min(5.0, b))
        params.sample_count = len(samples)
        params.last_updated = _utc_now()

    def save(self, path: Path) -> None:
        """保存校准参数到 JSON 文件。"""
        data = {
            "global_temperature": self.global_temperature,
            "min_samples_for_calibration": self.min_samples_for_calibration,
            "domain_params": {
                domain: params.to_dict()
                for domain, params in self.domain_params.items()
            },
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> ProbabilityCalibrator:
        """从 JSON 文件加载校准参数。"""
        if not path.exists():
            return cls()

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            domain_params = {
                domain: CalibrationParams.from_dict(params_dict)
                for domain, params_dict in data.get("domain_params", {}).items()
            }
            return cls(
                domain_params=domain_params,
                global_temperature=data.get("global_temperature", 1.0),
                min_samples_for_calibration=data.get("min_samples_for_calibration", 10),
            )
        except (json.JSONDecodeError, OSError, KeyError):
            return cls()


def _utc_now() -> str:
    """返回 UTC 时间戳字符串。"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ── 工厂函数：从历史反馈初始化校准器 ──────────────────────────
def build_calibrator_from_feedback_logs(
    cases_dir: Path,
    *,
    output_path: Path | None = None,
) -> ProbabilityCalibrator:
    """扫描 cases/ 下所有 prediction_feedback.jsonl，初始化校准器。

    Args:
        cases_dir: 案例目录
        output_path: 可选，保存校准参数的路径

    Returns:
        训练好的 ProbabilityCalibrator
    """
    calibrator = ProbabilityCalibrator()
    domain_samples: dict[str, list[tuple[float, bool]]] = {}

    for case_dir in cases_dir.iterdir():
        if not case_dir.is_dir():
            continue

        feedback_file = case_dir / "prediction_feedback.jsonl"
        if not feedback_file.exists():
            continue

        try:
            with feedback_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)

                    domain = entry.get("domain", "")
                    predicted_event = entry.get("predicted_event", "")
                    actual_result = entry.get("actual_result", "")
                    verdict = entry.get("verdict", "skip")

                    if not domain or verdict not in ("y", "n"):
                        continue

                    # 从 school_weights_before 推断预测概率（简化逻辑）
                    # 实际应从 prediction output 读取原始概率
                    school_weights = entry.get("school_weights_before", {})
                    if not school_weights:
                        continue

                    # 简化：取该领域所有流派权重均值作为预测概率代理
                    weights = list(school_weights.values())
                    predicted_prob = sum(weights) / len(weights) if weights else 0.5

                    actual_outcome = (verdict == "y")

                    domain_samples.setdefault(domain, []).append(
                        (predicted_prob, actual_outcome)
                    )

        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  读取 {feedback_file} 失败: {e}")
            continue

    # 批量拟合每个领域的 Platt 参数
    for domain, samples in domain_samples.items():
        if len(samples) >= calibrator.min_samples_for_calibration:
            calibrator.batch_fit_platt(domain, samples)
            print(f"✅ 已校准领域 {domain}，样本数={len(samples)}")

    if output_path:
        calibrator.save(output_path)
        print(f"💾 校准参数已保存至 {output_path}")

    return calibrator


# ── CLI 入口 ────────────────────────────────────────────────
def main() -> int:
    """命令行入口：训练并保存校准器。"""
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="v4.2 概率校准器训练")
    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=Path("cases"),
        help="案例目录",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("engine/calibration_params.json"),
        help="输出校准参数路径",
    )
    args = parser.parse_args()

    if not args.cases_dir.exists():
        print(f"❌ 案例目录不存在: {args.cases_dir}", file=sys.stderr)
        return 1

    print("🔧 开始训练概率校准器...")
    calibrator = build_calibrator_from_feedback_logs(
        args.cases_dir,
        output_path=args.output,
    )

    print(f"\n📊 校准器统计:")
    print(f"   已校准领域数: {len(calibrator.domain_params)}")
    print(f"   全局温度: {calibrator.global_temperature:.4f}")
    print("\n✅ 训练完成")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
