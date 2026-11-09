// Verhaal: jongeman geeft een deel van zijn geld aan een oudere man; teller daalt, maar Allah's rekening is anders.
window.STORY=function({tl,P,st,du,en,sfx,capAt,mouth,walk,R,$,handPos}){
  const T=k=>CFG.text[LANG][k];
  // oudere man zit verdrietig op de bank
  tl.set(P.el,{o:1},0);tl.set(P.el_h,{r:30},0);tl.set(P.el_u,{r:12},0);mouth('el_h','ms',0);
  tl.to(P.el_h,{r:34,duration:1.6,ease:'sine.inOut',yoyo:true,repeat:3},st('v3'));
  // teller: geld in zijn zak
  const c={v:0};$('cLabel').textContent=T('cLabel');
  const show=()=>{$('cVal').textContent=T('cur')+Math.round(c.v);};
  const S=st('v3');
  walk('ym',S-.6,3.4,760);                       // -160 -> 600
  tl.to(P.cam,{s:1.12,x:-40,y:-1060,duration:3,ease:'sine.inOut'},S-.8);
  tl.fromTo('#counter',{opacity:0,y:30},{opacity:1,y:0,duration:.5,immediateRender:false},S+.3);
  tl.fromTo(c,{v:0},{v:100,duration:1.2,ease:'power2.out',immediateRender:false,onUpdate:show,onUpdateParams:[]},S+.4);
  sfx(S+.4,'coin');sfx(S+.8,'coin');
  // geven
  const G=st('v4')+du('v4')*.45;
  capAt(T('c4'),st('v4'),en('v4')+.3,300);
  tl.to('#counter',{y:40,scale:.85,duration:.5},st('v4'));
  tl.to(P.ym_h,{r:12,duration:.4},st('v4')+.2);mouth('ym_h','ms',st('v4')+.2);
  tl.to(P.ym_af,{r:-48,duration:.6,ease:'back.out(1.3)'},G-.2).to(P.ym_af_f,{r:-25,duration:.6},G-.2);
  tl.to(P.el_h,{r:6,duration:.6},G-.4).to(P.el_u,{r:4,duration:.6},G-.4);
  tl.to(P.el_af,{r:-60,duration:.6},G-.1).to(P.el_af_f,{r:-40,duration:.6},G-.1);
  for(let i=0;i<5;i++){const co=P['co'+i];const t=G+.35+i*.12;
    tl.set(co,{x:690,y:2235,o:1,s:.8},t);
    tl.to(co,{x:742,duration:.45,ease:'power1.inOut'},t);
    tl.to(co,{y:2195,duration:.22,ease:'power2.out'},t).to(co,{y:2262,duration:.23,ease:'power2.in'},t+.22);
    tl.to(co,{o:0,duration:.1},t+.45);sfx(t+.4,'coin');}
  tl.to(c,{v:70,duration:.8,ease:'power2.inOut',onUpdate:show},G+.4);
  tl.fromTo('#cDelta',{opacity:0,y:0},{opacity:1,y:-20,duration:.4,immediateRender:false},G+.5).to('#cDelta',{opacity:0,duration:.4},G+2);
  $('cDelta').textContent='−'+T('cur')+'30';
  tl.to('#cVal',{webkitTextStroke:'3px #ff5a4a',duration:.3},G+.5);
  // oude man blij, dua
  mouth('el_h','mh',G+.9);
  tl.to(P.el_af,{r:-40,duration:.7,ease:'back.out(1.4)'},G+1.2).to(P.el_af_f,{r:-122,duration:.7,ease:'back.out(1.4)'},G+1.2);
  tl.to(P.el_ab,{r:-30,duration:.7,ease:'back.out(1.4)'},G+1.3).to(P.el_ab_f,{r:-126,duration:.7,ease:'back.out(1.4)'},G+1.3);
  tl.to(P.el_h,{r:-10,duration:.6},G+1.3);
  tl.to(P.ym_af,{r:0,duration:.6},G+1.2).to(P.ym_af_f,{r:0,duration:.6},G+1.2).to(P.ym_h,{r:0,duration:.5},G+1.2);mouth('ym_h','mh',G+1.3);
  // "op papier minder"
  capAt(T('c5'),st('v5'),en('v5')+.3,300);
  tl.to('#counter',{y:0,scale:1.05,duration:.5},st('v5')-.2);
  tl.to('#cVal',{x:6,duration:.05,repeat:9,yoyo:true,ease:'none'},st('v5')+.3);
  // Allah's rekening: terug naar 100 + barakah
  const B=st('v6');capAt(T('c6'),B,en('v6')+.4,300);
  tl.to(c,{v:100,duration:1.4,ease:'power2.out',onUpdate:show},B+.6);
  tl.to('#cVal',{webkitTextStroke:'3px #f2c46d',color:'rgba(242,196,109,.25)',duration:.6},B+.6);
  tl.to('#cLabel',{opacity:0,duration:.3},B+.6);
  tl.call(()=>{},null,B+.6);
  tl.fromTo('#cDelta',{opacity:0,y:20},{opacity:1,y:0,duration:.5,immediateRender:false},B+1.4);
  tl.set('#cDelta',{color:'#f2c46d'},B+1.39);
  tl.call(()=>{$('cDelta').textContent=T('bereket');},null,B+1.39);
  tl.fromTo(P.halo,{o:0,s:.5},{o:.9,s:1,duration:2,ease:'power2.out',immediateRender:false},B+.6);
  tl.to('#flash',{opacity:.25,duration:.1},B+.6).to('#flash',{opacity:0,duration:.6},B+.7);
  sfx(B+.6,'shimmer');
  tl.to('#counter',{opacity:0,y:-40,duration:.4},st('v7')-.5);
  tl.to(P.cam,{s:1.22,x:-80,y:-1110,duration:2.5,ease:'sine.inOut'},B);
  [P.el_af,P.el_ab].forEach(a=>tl.to(a,{r:-24,duration:.6},st('v7')-.6));tl.to([P.el_af_f,P.el_ab_f],{r:-62,duration:.6},st('v7')-.6);
  // texts set by seek (tl.call is skipped by seek): keep counter text in sync each frame
  window.__extraRender=()=>{show();$('cDelta').textContent=(window.__t||0)>=B+1.39?T('bereket'):'−'+T('cur')+'30';};
};
