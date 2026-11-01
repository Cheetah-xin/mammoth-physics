export const PERSON=60, ITEM=10;
export function initial(){return {x:4,v:0,items:[],remaining:3,t:0,won:false,impulse:0};}
export function toss(s,direction,speed){if(!s.remaining||s.won)return false;const before=PERSON+ITEM*s.remaining;const old=s.v;s.remaining--;s.v=old-direction*ITEM*speed/before;s.items.push({x:s.x,v:s.v+direction*speed});return true;}
export function step(s,dt){if(s.won)return;s.t+=dt;s.x+=s.v*dt;for(const i of s.items){i.x+=i.v*dt;if(i.x<.25){i.x=.25;i.v=Math.abs(i.v);}if(i.x>11.75){i.x=11.75;i.v=-Math.abs(i.v);}}if(s.x<.35||s.x>11.65){const prev=s.v;s.x=Math.max(.35,Math.min(11.65,s.x));s.v=-s.v;s.impulse+=(PERSON+ITEM*s.remaining)*(s.v-prev);}}
export function grab(s){if(s.x<10.1||s.x>11.6||s.won)return false;s.impulse-=(PERSON+ITEM*s.remaining)*s.v;s.v=0;s.won=true;return true;}
export function momentum(s,system){if(system==='person')return PERSON*s.v;return (PERSON+ITEM*s.remaining)*s.v+s.items.reduce((p,i)=>p+ITEM*i.v,0);}
