// Verhaal: man verliest zijn portemonnee; jongeman raapt hem op en geeft hem terug -> "Allah seni hayırla mükâfatlandırsın!"
window.STORY=function({tl,P,st,du,en,sfx,capAt,bubble,mouth,walk,setWalker,$,GROUND}){
  const T=k=>CFG.text[LANG][k];
  // pa loopt nu van links naar rechts (kijkt naar rechts)
  P.pa.sx=1;P.pa.bx=-300;setWalker('pa',1);
  tl.set(P.wal,{o:1,follow:2},0);
  const S=st('v3');
  capAt(T('c3'),S,en('v3')+.3,300);
  walk('pa',S-1,3.4,1100);                 // -300 -> 800
  const D=S+du('v3')*.5;                   // portemonnee valt
  tl.set(P.wal,{follow:0},D);
  tl.to(P.wal,{y:GROUND-14,duration:.5,ease:'bounce.out'},D).to(P.wal,{r:80,duration:.4},D);sfx(D+.15,'thud');
  tl.to(P.cam,{s:1.1,x:0,y:-1050,duration:2.5,ease:'sine.inOut'},S-.8);
  // jongeman komt aanlopen, hurkt en raapt op
  const A=st('v4');capAt(T('c4'),A,en('v4')+.3,300);
  walk('ym',D+.2,A-D+.4,480);              // -160 -> 320 (vlak voor de portemonnee)
  const K=A+.6;
  tl.to(P.ym_h,{r:20,duration:.4},K-.5);mouth('ym_h','ms',K-.5);
  tl.to(P.ym_u,{r:40,y:80,duration:.6,ease:'power2.inOut'},K);
  tl.to(P.ym_sk,{y:80,sy:.8,k:-8,duration:.6,ease:'power2.inOut'},K);
  tl.to([P.ym_lf,P.ym_lb],{y:80,duration:.6,ease:'power2.inOut'},K);
  tl.to(P.ym_lf,{r:-60,duration:.6},K).to(P.ym_lf_s,{r:92,duration:.6},K);
  tl.to(P.ym_lb,{r:-10,duration:.6},K).to(P.ym_lb_s,{r:76,duration:.6},K);
  tl.to(P.ym_af,{r:-30,duration:.6},K).to(P.ym_af_f,{r:-12,duration:.6},K);
  tl.set(P.wal,{follow:1,r:0},K+.65);sfx(K+.65,'pop');
  const U=K+1.0;
  tl.to(P.ym_u,{r:0,y:0,duration:.6},U).to(P.ym_sk,{y:0,sy:1,k:0,duration:.6},U);
  tl.to([P.ym_lf,P.ym_lb,P.ym_lf_s,P.ym_lb_s],{r:0,y:0,duration:.6},U);
  tl.to(P.ym_af,{r:-20,duration:.5},U).to(P.ym_af_f,{r:-60,duration:.5},U).to(P.ym_h,{r:0,duration:.4},U);
  // pa merkt het, draait zich om
  tl.to(P.pa_h,{r:-8,duration:.3},U+.2);tl.set(P.pa,{sx:-1},U+.5);
  walk('ym',U+.7,1.3,640);                 // -> 480
  tl.to(P.cam,{s:1.18,x:-80,y:-1090,duration:2,ease:'sine.inOut'},U+.3);
  // teruggeven
  const G=en('v4')-.2;
  tl.to(P.ym_af,{r:-62,duration:.5,ease:'back.out(1.3)'},G).to(P.ym_af_f,{r:-10,duration:.5},G);
  tl.to(P.pa_af,{r:-50,duration:.5},G+.2).to(P.pa_af_f,{r:-20,duration:.5},G+.2);
  tl.set(P.wal,{follow:2},G+.75);sfx(G+.75,'pop');mouth('ym_h','mh',G+.4);
  // dankwoord
  const D2=st('v5');mouth('pa_h','mh',D2-.3);
  tl.to(P.pa_af,{r:5,duration:.5},D2-.2).to(P.pa_af_f,{r:-155,duration:.5},D2-.2).to(P.ym_af,{r:0,duration:.5},D2-.2).to(P.ym_af_f,{r:0,duration:.5},D2-.2);
  tl.to(P.pa_h,{r:6,duration:.3,yoyo:true,repeat:1},D2+.2);
  bubble(T('b1'),300,520,'r',D2,en('v5')+1.2);
  // het is een dua: Arabische kalligrafie
  const W=st('v6');capAt(T('c6'),W,en('v6')+.3,300);
  $('arBig').textContent='جَزَاكَ ٱللَّهُ خَيْرًا';$('arBig').style.top='520px';
  tl.fromTo('#arBig',{opacity:0,scale:1.3,filter:'blur(16px)'},{opacity:1,scale:1,filter:'blur(0px)',duration:1,immediateRender:false},W+du('v6')*.45);
  tl.to('#arBig',{opacity:0,duration:.4},st('v7')-.5);
  tl.fromTo(P.halo,{o:0,s:.5},{o:.9,s:1,duration:2,ease:'power2.out',immediateRender:false},W+du('v6')*.45);
  sfx(W+du('v6')*.45,'shimmer');
  tl.to(P.cam,{s:1.26,y:-1130,duration:2.4,ease:'sine.inOut'},W);
  tl.to([P.pa_af,P.pa_af_f],{r:0,duration:.6},st('v7')-.6);
};
