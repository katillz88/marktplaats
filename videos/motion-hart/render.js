// Rendert de motion graphics-video beeld-voor-beeld naar MP4 (1080x1920, 60fps).
// Gebruik: node render.js tr|en            -> volledige video
//          node render.js tr --stills 1,5,9 -> losse PNG's ter controle
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

const LANG = process.argv[2] || 'tr';
const DIR = __dirname;
const FPS = 60;
const WORKERS = 4;
const OUT = path.join(DIR, 'out', LANG);
const FRAMES = path.join(OUT, 'frames');

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(DIR, 'index.html') + '?lang=' + LANG);
  await page.waitForFunction(() => window.__ready === true);
  return page;
}

async function main() {
  fs.rmSync(FRAMES, { recursive: true, force: true });
  fs.mkdirSync(FRAMES, { recursive: true });
  const browser = await chromium.launch();
  const si = process.argv.indexOf('--stills');
  if (si > -1) {
    const page = await openPage(browser);
    for (const t of process.argv[si + 1].split(',').map(Number)) {
      await page.evaluate(t => window.__seek(t), t);
      await page.screenshot({ path: path.join(OUT, `still_${t}.png`) });
    }
    await browser.close();
    return;
  }
  const probe = await openPage(browser);
  const duration = await probe.evaluate(() => window.__duration);
  const sfx = await probe.evaluate(() => window.__sfx);
  const cues = await probe.evaluate(() => window.CUES);
  await probe.close();
  const total = Math.round(duration * FPS);
  let next = 0;
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    const page = await openPage(browser);
    while (next < total) {
      const i = next++;
      await page.evaluate(t => window.__seek(t), i / FPS);
      await page.screenshot({ path: path.join(FRAMES, `f${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 95 });
    }
  }));
  await browser.close();

  // ---- Geluid: voice-over + klankondergrond + sound design (whoosh, boom, shimmer, shatter, hartslag) ----
  const D = duration.toFixed(2);
  const args = ['-y'];
  let n = 0;
  const add = (spec, lavfi = true) => { if (lavfi) args.push('-f', 'lavfi'); args.push('-i', spec); return n++; };
  const SND = {
    whoosh: { src: 'anoisesrc=color=pink:amplitude=0.6:duration=1.1', fx: 'bandpass=f=1100:width_type=o:w=2.5,afade=t=in:d=0.55,afade=t=out:st=0.55:d=0.55,volume=0.55' },
    boom: { src: "aevalsrc='0.9*sin(2*PI*(38+70*exp(-9*t))*t)*exp(-3.5*t)':d=1.2:s=48000", fx: 'volume=0.9' },
    shimmer: { src: "aevalsrc='0.12*(sin(2*PI*1568*t)+sin(2*PI*2093*t)+sin(2*PI*2637*t)+0.6*sin(2*PI*3136*t))*exp(-1.2*t)*(1-exp(-12*t))':d=2.4:s=48000", fx: 'aecho=0.8:0.7:90|180:0.4|0.25,volume=0.7' },
    shatter: { src: 'anoisesrc=color=white:amplitude=0.7:duration=0.7', fx: 'highpass=f=2500,afade=t=out:st=0.02:d=0.65,volume=0.45' },
    beat: { src: "aevalsrc='sin(2*PI*52*t)*exp(-13*t)+0.4*sin(2*PI*90*t)*exp(-20*t)':d=0.4:s=48000", fx: 'volume=1.1' },
  };
  const pad = [146.83, 220, 293.66, 369.99].map(f => add(`sine=frequency=${f}:duration=${D}`));
  const ev = sfx.map(e => ({ ...e, idx: add(SND[e.type].src) }));
  const vo = Object.keys(cues).map(k => ({ k, t: cues[k][0], idx: add(path.join(DIR, 'voice', LANG, k + '.wav'), false) }));
  let f = '';
  pad.forEach((i, k) => { f += `[${i}]volume=${[0.15, 0.09, 0.06, 0.045][k]},tremolo=f=${0.11 + k * 0.04}:d=0.35[p${k}];`; });
  f += `${pad.map((_, k) => `[p${k}]`).join('')}amix=inputs=${pad.length}:normalize=0,lowpass=f=1300,aecho=0.8:0.8:180|360|720:0.35|0.25|0.15,afade=t=in:d=2.5,afade=t=out:st=${(duration - 2.5).toFixed(2)}:d=2.5[padm];`;
  ev.forEach((e, k) => { const ms = Math.round(e.t * 1000); f += `[${e.idx}]${SND[e.type].fx},aformat=channel_layouts=stereo:sample_rates=48000,adelay=${ms}|${ms}[e${k}];`; });
  f += `[padm]${ev.map((_, k) => `[e${k}]`).join('')}amix=inputs=${1 + ev.length}:normalize=0,aformat=channel_layouts=stereo:sample_rates=48000[bg];`;
  vo.forEach((v, k) => { const ms = Math.round(v.t * 1000); f += `[${v.idx}]aresample=48000,adelay=${ms}|${ms}[v${k}];`; });
  f += `${vo.map((_, k) => `[v${k}]`).join('')}amix=inputs=${vo.length}:normalize=0,highpass=f=80,equalizer=f=3000:t=q:w=1:g=3,volume=1.3,aformat=channel_layouts=stereo:sample_rates=48000,apad=whole_dur=${D},asplit=2[vo][sc];`;
  f += `[bg][sc]sidechaincompress=threshold=0.03:ratio=5:attack=40:release=400[duck];`;
  f += `[duck][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]`;
  const audio = path.join(OUT, 'mix.wav');
  args.push('-filter_complex', f, '-map', '[a]', '-t', D, '-ar', '48000', audio);
  execFileSync('ffmpeg', args, { stdio: ['ignore', 'ignore', 'inherit'] });

  const mp4 = path.join(DIR, `hart-${LANG}.mp4`);
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-framerate', String(FPS), '-i', path.join(FRAMES, 'f%05d.jpg'), '-i', audio,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', D, mp4], { stdio: 'inherit' });
  fs.rmSync(FRAMES, { recursive: true, force: true });
  console.log('Klaar:', mp4);
}
main().catch(e => { console.error(e); process.exit(1); });
