#!/usr/bin/env node
/**
 * 紫微 v4.0 解读数据集只读查表器（不写任何文件）
 *
 *   node ziwei_reader.mjs <dataDir> <year> <key> [dims_csv] [plain|zst]
 *   node ziwei_reader.mjs <dataDir> <year> --build-index
 *
 * 输出单行 JSON 到 stdout。默认优先读已解压的 year-YYYY.jsonl（seek 到 offset）；
 * 传 zst 时强制走 zstd 流式解压路径（验收用），读到 [offset, offset+length)
 * 即截取并销毁流，不落地 700 MB 明文。
 *
 * --build-index：缺失 idx 时，流式解压 zst 并逐行扫 k 键，把索引 JSON 直接输出到
 * stdout（由调用方决定写到哪）；全程不写文件、不生成明文分片。语义与上游
 * scripts/dataset/build-index.mjs 完全一致：index[k] = [明文字节偏移, 不含换行的行长]。
 *
 * 依赖：Node >= 22（zlib.createZstdDecompress），无 npm 依赖。
 */
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const [dataDir, year, key, dimsCsv, prefer] = process.argv.slice(2);

function die(message) {
  process.stdout.write(JSON.stringify({ ok: false, error: message }) + '\n');
  process.exit(1);
}

if (!dataDir || !year || !key) {
  die('用法: node ziwei_reader.mjs <dataDir> <year> <key> [dims_csv]');
}

const idxPath = path.join(dataDir, `year-${year}.idx.json`);
const zstPath = path.join(dataDir, `year-${year}.jsonl.zst`);
const jsonlPath = path.join(dataDir, `year-${year}.jsonl`);

// 缺失索引时按需重建：只输出 JSON，不落盘（写文件是 CLI 的显式动作）
if (key === '--build-index') {
  const srcPath = fs.existsSync(jsonlPath) ? jsonlPath : zstPath;
  if (!fs.existsSync(srcPath)) {
    die(`缺数据分片 ${zstPath}；先运行 python -m tools.ziwei_fetch --year ${year} --download`);
  }
  const index = {};
  let pending = Buffer.alloc(0);
  let pendingStart = 0;
  let count = 0;
  const stream = srcPath.endsWith('.zst')
    ? fs.createReadStream(srcPath).pipe(
        zlib.createZstdDecompress({ maxOutputLength: 4 * 1024 ** 3 }),
      )
    : fs.createReadStream(srcPath);
  try {
    for await (const chunk of stream) {
      const buf = Buffer.concat([pending, chunk]);
      let start = 0;
      let nl;
      while ((nl = buf.indexOf(0x0A, start)) !== -1) {
        const len = nl - start;
        if (len > 0) {
          const head = buf.toString('utf8', start, start + Math.min(len, 80));
          const m = /^\{"k":"([^"]+)"/.exec(head);
          if (m) {
            index[m[1]] = [pendingStart + start, len];
            count += 1;
          }
        }
        start = nl + 1;
      }
      pending = Buffer.from(buf.subarray(start));
      pendingStart += start;
    }
    if (pending.length > 0) {
      const head = pending.toString('utf8', 0, Math.min(pending.length, 80));
      const m = /^\{"k":"([^"]+)"/.exec(head);
      if (m) {
        index[m[1]] = [pendingStart, pending.length];
        count += 1;
      }
    }
  } catch (e) {
    die(`流式建索引失败: ${e.message}`);
  }
  process.stdout.write(JSON.stringify({
    ok: true,
    mode: 'build-index',
    shard: path.basename(srcPath),
    count,
    index,
  }) + '\n');
  process.exit(0);
}

if (!fs.existsSync(idxPath)) {
  die(`缺索引 ${idxPath}；先运行 python -m tools.ziwei_fetch --year ${year} --download`);
}

let idx;
try {
  idx = JSON.parse(fs.readFileSync(idxPath, 'utf-8'));
} catch (e) {
  die(`索引不可读: ${e.message}`);
}

const hit = idx[key];
if (!hit) die(`该年分片中没有 ${key}`);
const [offset, length] = hit;

async function readZstdRange(filePath, off, len) {
  if (typeof zlib.createZstdDecompress !== 'function') {
    throw new Error('需要 Node >= 22（zlib.createZstdDecompress 内置 zstd）');
  }
  const rs = fs.createReadStream(filePath);
  const dec = zlib.createZstdDecompress({ maxOutputLength: 2 * 1024 ** 3 });
  rs.pipe(dec);
  let pos = 0;
  const parts = [];
  try {
    for await (const chunk of dec) {
      const start = pos;
      pos += chunk.length;
      if (pos > off) {
        const a = Math.max(off - start, 0);
        const b = Math.min(off + len - start, chunk.length);
        if (b > a) parts.push(chunk.subarray(a, b));
      }
      if (pos >= off + len) {
        rs.destroy();
        break;
      }
    }
  } catch (e) {
    if (e.code !== 'ERR_STREAM_PREMATURE_CLOSE') throw e;
  }
  if (pos < off + len) throw new Error('分片解压后长度小于索引 offset，索引与数据不匹配');
  return Buffer.concat(parts);
}

let buf;
let shard;
if (prefer !== 'zst' && fs.existsSync(jsonlPath)) {
  const fd = fs.openSync(jsonlPath, 'r');
  buf = Buffer.alloc(length);
  fs.readSync(fd, buf, 0, length, offset);
  fs.closeSync(fd);
  shard = path.basename(jsonlPath);
} else if (fs.existsSync(zstPath)) {
  try {
    buf = await readZstdRange(zstPath, offset, length);
  } catch (e) {
    die(`流式解压失败: ${e.message}`);
  }
  shard = path.basename(zstPath);
} else {
  die(`缺数据分片 ${zstPath}；先运行 ziwei-doushu 的 node scripts/dataset/fetch.mjs ${year} --zst-only`);
}

let rec;
try {
  rec = JSON.parse(buf.toString('utf-8'));
} catch (e) {
  die(`记录解析失败（offset=${offset}, length=${length}）: ${e.message}`);
}
if (rec.k !== key) die(`键不匹配：期望 ${key}，实得 ${rec.k}`);

const dims = dimsCsv ? dimsCsv.split(',').map((s) => s.trim()).filter(Boolean) : [];
const c = {};
for (const d of dims) {
  if (!(d in rec.c)) die(`无此维度: ${d}（可选 ${Object.keys(rec.c).join(' / ')}）`);
  c[d] = rec.c[d];
}

process.stdout.write(JSON.stringify({
  ok: true,
  locator: {
    shard,
    index_file: path.basename(idxPath),
    key,
    offset,
    length,
  },
  record: {
    k: rec.k, y: rec.y, m: rec.m, d: rec.d, h: rec.h, g: rec.g,
    ms: rec.ms ?? null,
    t: rec.t,
    c,
  },
  dims_requested: dims,
  dims_available: Object.keys(rec.c),
  text_chars_total: Object.values(rec.t).reduce((a, b) => a + b, 0),
}) + '\n');
