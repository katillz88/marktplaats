// Rendert index.html beeld-voor-beeld naar MP4 (1080x1920, 30fps).
// Gebruik: node render.js            -> volledige video
//          node render.js --stills 0,5,12,19,27  -> losse PNG's ter controle
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

const DIR = __dirname;
const FPS = 60;
const WORKERS = 4;
const OUT = path.join(DIR, 'out');
const FRAMES = path.join(OUT, 'frames');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(DIR, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => typeof window.__seek === 'function');
  return page;
}

async function main() {
  fs.mkdirSync(FRAMES, { recursive: true });
  const browser = await chromium.launch();
  const stillsArg = process.argv.indexOf('--stills');
  if (stillsArg > -1) {
    const page = await openPage(browser);
    for (const t of process.argv[stillsArg + 1].split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), t);
      await page.screenshot({ path: path.join(OUT, `still_${t}.png`) });
    }
    await browser.close();
    return;
  }
  const duration = 31;
  const total = Math.round(duration * FPS);
  let next = 0;
  const t0 = Date.now();
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    const page = await openPage(browser);
    while (next < total) {
      const i = next++;
      await page.evaluate(t => window.__seek(t), i / FPS);
      await page.screenshot({ path: path.join(FRAMES, `f${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 95 });
      if (i % 300 === 0) console.log(`frame ${i}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
  }));
  await browser.close();

  // Geluid: Turkse voice-over + zachte klankondergrond (geen melodie/beat), vogels, wind en whooshes.
  // De achtergrond wordt automatisch zachter wanneer de stem spreekt (sidechain).
  const audio = path.join(OUT, 'mix.wav');
  const V = { v1: 0.4, v2: 2.4, v3: 5.4, v4: 8.0, v5: 11.0, v6: 14.5, v7: 17.6, v8: 19.7, v9: 25.95 };
  const args = ['-y'];
  const inputs = [];
  const add = (spec, lavfi = true) => { if (lavfi) args.push('-f', 'lavfi'); args.push('-i', spec); return inputs.push(spec) - 1; };
  const pad = [146.83, 220, 293.66, 369.99].map(f => add(`sine=frequency=${f}:duration=31`));
  const pad2 = [440, 587.33].map(f => add(`sine=frequency=${f}:duration=8`));
  const wind = add('anoisesrc=color=brown:amplitude=0.6:duration=31:seed=3');
  const wh = [1.6, 2.2, 1.2].map((d, k) => add(`anoisesrc=color=pink:amplitude=0.5:duration=${d}:seed=${5 + k}`));
  const thud = add('sine=frequency=70:duration=0.35');
  const chirp = add("aevalsrc='0.5*sin(2*PI*(3300+900*sin(2*PI*30*t))*t)*exp(-14*t)':d=0.3:s=48000");
  const voice = Object.keys(V).map(k => add(path.join(DIR, 'voice', k + '.wav'), false));
  const birdsAt = [4.9, 5.15, 6.8, 9.4, 9.6, 12.3, 13.1, 13.3, 15.9, 16.2];
  let f = '';
  pad.forEach((n, k) => { f += `[${n}]volume=${[0.16, 0.10, 0.07, 0.05][k]},tremolo=f=${0.11 + k * 0.04}:d=0.35[p${k}];`; });
  pad2.forEach((n, k) => { f += `[${n}]volume=0.05,afade=t=in:d=2.5,afade=t=out:st=5.5:d=2.5,adelay=18000|18000[q${k}];`; });
  f += `${pad.map((_, k) => `[p${k}]`).join('')}${pad2.map((_, k) => `[q${k}]`).join('')}amix=inputs=${pad.length + pad2.length}:normalize=0,lowpass=f=1400,aecho=0.8:0.8:180|360|720:0.35|0.25|0.15,afade=t=in:d=3,afade=t=out:st=28.5:d=2.5[padm];`;
  f += `[${wind}]lowpass=f=380,highpass=f=50,volume=0.35,afade=t=in:d=2,afade=t=out:st=28.5:d=2.5[wind];`;
  const whAt = [2500, 18000, 25500];
  wh.forEach((n, k) => { f += `[${n}]bandpass=f=${[900, 1400, 1100][k]}:width_type=o:w=2,afade=t=in:d=${[0.9, 1.2, 0.4][k]},afade=t=out:st=${[0.9, 1.2, 0.4][k]}:d=${[0.7, 1.0, 0.8][k]},volume=0.6,adelay=${whAt[k]}|${whAt[k]}[w${k}];`; });
  f += `[${thud}]afade=t=out:st=0.05:d=0.3,volume=1.0,adelay=6250|6250[thud];`;
  f += `[${chirp}]asplit=${birdsAt.length}${birdsAt.map((_, k) => `[c${k}]`).join('')};`;
  birdsAt.forEach((t, k) => { const ms = Math.round(t * 1000); f += `[c${k}]volume=${0.10 + (k % 3) * 0.04},adelay=${ms}|${ms}[b${k}];`; });
  f += `[padm][wind]${wh.map((_, k) => `[w${k}]`).join('')}[thud]${birdsAt.map((_, k) => `[b${k}]`).join('')}amix=inputs=${3 + wh.length + birdsAt.length}:normalize=0,aformat=channel_layouts=stereo:sample_rates=48000[bg];`;
  Object.keys(V).forEach((k, idx) => { const ms = Math.round(V[k] * 1000); f += `[${voice[idx]}]aresample=48000,adelay=${ms}|${ms}[v${idx}];`; });
  f += `${voice.map((_, k) => `[v${k}]`).join('')}amix=inputs=${voice.length}:normalize=0,highpass=f=80,equalizer=f=3000:t=q:w=1:g=3,aecho=0.9:0.5:40:0.15,volume=1.6,aformat=channel_layouts=stereo:sample_rates=48000,apad=whole_dur=31,asplit=2[vo][sc];`;
  f += `[bg][sc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=400[duck];`;
  f += `[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=9[a]`;
  args.push('-filter_complex', f, '-map', '[a]', '-t', '31', '-ar', '48000', audio);
  execFileSync('ffmpeg', args, { stdio: ['ignore', 'ignore', 'inherit'] });

  const mp4 = path.join(DIR, 'islamitische-short.mp4');
  execFileSync('ffmpeg', ['-y', '-framerate', String(FPS), '-i', path.join(FRAMES, 'f%05d.jpg'), '-i', audio,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', mp4], { stdio: 'inherit' });
  console.log('Klaar:', mp4);
}
main().catch(e => { console.error(e); process.exit(1); });
