// Rendert index.html beeld-voor-beeld naar MP4 (1080x1920, 30fps).
// Gebruik: node render.js            -> volledige video
//          node render.js --stills 0,5,12,19,27  -> losse PNG's ter controle
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

const DIR = __dirname;
const FPS = 30;
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
  const duration = 30;
  const total = Math.round(duration * FPS);
  let next = 0;
  const t0 = Date.now();
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    const page = await openPage(browser);
    while (next < total) {
      const i = next++;
      await page.evaluate(t => window.__seek(t), i / FPS);
      await page.screenshot({ path: path.join(FRAMES, `f${String(i).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 95 });
      if (i % 100 === 0) console.log(`frame ${i}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
  }));
  await browser.close();

  // Geluid: zacht windgeruis + whooshes bij scènewissels + plof bij vallende tas (geen muziek)
  const audio = path.join(OUT, 'ambience.wav');
  execFileSync('ffmpeg', ['-y',
    '-f', 'lavfi', '-i', 'anoisesrc=color=brown:amplitude=0.6:duration=30:seed=3',
    '-f', 'lavfi', '-i', 'anoisesrc=color=pink:amplitude=0.5:duration=1.6:seed=5',
    '-f', 'lavfi', '-i', 'anoisesrc=color=pink:amplitude=0.5:duration=2.2:seed=9',
    '-f', 'lavfi', '-i', 'anoisesrc=color=pink:amplitude=0.5:duration=1.2:seed=11',
    '-f', 'lavfi', '-i', 'sine=frequency=70:duration=0.35',
    '-filter_complex',
    '[0]lowpass=f=420,highpass=f=50,volume=0.55,afade=t=in:d=2,afade=t=out:st=27.5:d=2.5[bed];' +
    '[1]bandpass=f=900:width_type=o:w=2,afade=t=in:d=0.9,afade=t=out:st=0.9:d=0.7,volume=0.9,adelay=2500|2500[w1];' +
    '[2]bandpass=f=1400:width_type=o:w=2,afade=t=in:d=1.2,afade=t=out:st=1.2:d=1.0,volume=0.7,adelay=18200|18200[w2];' +
    '[3]bandpass=f=1100:width_type=o:w=2,afade=t=in:d=0.4,afade=t=out:st=0.4:d=0.8,volume=0.9,adelay=25000|25000[w3];' +
    '[4]afade=t=out:st=0.05:d=0.3,volume=1.2,adelay=6250|6250[thud];' +
    '[bed][w1][w2][w3][thud]amix=inputs=5:normalize=0,alimiter=limit=0.8,aformat=channel_layouts=stereo[a]',
    '-map', '[a]', '-t', '30', '-ar', '48000', audio], { stdio: 'inherit' });

  const mp4 = path.join(DIR, 'islamitische-short.mp4');
  execFileSync('ffmpeg', ['-y', '-framerate', String(FPS), '-i', path.join(FRAMES, 'f%04d.jpg'), '-i', audio,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', mp4], { stdio: 'inherit' });
  console.log('Klaar:', mp4);
}
main().catch(e => { console.error(e); process.exit(1); });
