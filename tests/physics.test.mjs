import test from 'node:test';import assert from 'node:assert/strict';import {initial,toss,step,grab,momentum} from '../public/physics.mjs';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
test('throw conserves total momentum and sets relative speed',()=>{const s=initial();toss(s,-1,6);near(momentum(s,'all'),0);near(s.items[0].v-s.v,-6);assert.ok(s.v>0);toss(s,1,4);near(momentum(s,'all'),0);});
test('no force means uniform motion',()=>{const s=initial();toss(s,-1,6);const v=s.v;step(s,.1);near(s.v,v);near(s.x,4+v*.1);});
test('grip only works in exit and stops player',()=>{const s=initial();assert.equal(grab(s),false);toss(s,-1,6);for(let i=0;i<1000&&s.x<10.1;i++)step(s,.02);assert.equal(grab(s),true);near(s.v,0);assert.equal(s.won,true);assert.equal(s.remaining,2);});
test('wall supplies impulse and reverses motion',()=>{const s=initial();s.x=11.64;s.v=1;step(s,.1);near(s.v,-1);assert.ok(s.impulse<0);});
test('inventory cannot become negative',()=>{const s=initial();for(let i=0;i<5;i++)toss(s,-1,6);assert.equal(s.remaining,0);assert.equal(s.items.length,3);});
import {reactionReadings} from '../public/learning.mjs';
test('system selection changes accounting but never the scale',()=>{assert.deepEqual(reactionReadings(10,true,false),{scale:90,selected:90});assert.deepEqual(reactionReadings(10,true,true),{scale:90,selected:100});assert.deepEqual(reactionReadings(10,false,true),{scale:90,selected:10});});
