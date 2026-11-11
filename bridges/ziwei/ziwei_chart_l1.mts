/**
 * L1 结构化盘面 runner：直接调用紫微项目 lib/ziwei/algorithm.ts 的 generateChart。
 *
 *   node --import tsx ziwei_chart_l1.mts <projectDir> <year> <month> <day> <hour> <gender>
 *
 * - 运行目录必须是紫微项目根（cwd），以便 `tsx` 与 `iztro` / `lunar-javascript` 解析到它的 node_modules。
 * - 只读：不写任何文件、不联网、不启动 Next.js 服务。
 * - 输出单行 JSON：{ ok, chart, generator }；失败为 { ok:false, error }。
 * - hour 是时辰地支索引 0=子…11=亥，与 case_key.hour_index 同源。
 *
 * 代码侧依赖为紫微项目自身（MIT）的 tsx / iztro，Python 侧零新增依赖。
 */
import { pathToFileURL } from 'node:url';

const [projectDir, y, m, d, h, g] = process.argv.slice(2);

function out(payload: unknown) {
  process.stdout.write(JSON.stringify(payload) + '\n');
}

if (!projectDir || !y || !m || !d || !h || !g) {
  out({ ok: false, error: '用法: node --import tsx ziwei_chart_l1.mts <projectDir> <year> <month> <day> <hour> <gender>' });
  process.exit(1);
}

try {
  const url = pathToFileURL(`${projectDir.replace(/[\\/]+$/, '')}/lib/ziwei/algorithm.ts`).href;
  const mod: any = await import(url);
  if (typeof mod.generateChart !== 'function') {
    throw new Error('lib/ziwei/algorithm.ts 未导出 generateChart；紫微项目版本不匹配');
  }
  const chart = mod.generateChart({
    year: Number(y),
    month: Number(m),
    day: Number(d),
    hour: Number(h),
    gender: g,
  });
  out({
    ok: true,
    chart,
    generator: {
      file: 'lib/ziwei/algorithm.ts',
      function: 'generateChart',
      runtime: 'node --import tsx',
      input: { year: Number(y), month: Number(m), day: Number(d), hour: Number(h), gender: g },
    },
  });
} catch (e) {
  out({ ok: false, error: e instanceof Error ? e.message : String(e) });
  process.exit(1);
}
