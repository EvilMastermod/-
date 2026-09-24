const express=require('express'),fs=require('fs'),path=require('path');
const app=express(); app.use(express.json({limit:'512kb'}));

const PORT=Number(process.env.PORT||3000), DIR=process.env.DATA_DIR||'/data';
const FILE=path.join(DIR,'spooky-prices.json');
const FRESH=Number(process.env.PRICE_FRESH_MS||7200000), RETAIN=Number(process.env.PRICE_RETAIN_MS||259200000);
const ALLOWED=/^\/an(?:10[1-8]|20[1-9]|30[1-9])$/i;

let db={version:3,listings:[],wallets:{}},saveTimer=null;

function strip(v){return String(v??'').replace(/§[0-9A-FK-OR]/gi,'').replace(/\u00a0/g,' ').trim()}
function norm(v){return strip(v).toLowerCase().replace(/ё/g,'е').replace(/[^a-zа-я0-9+ _-]/gi,' ').replace(/\s+/g,' ').trim()}
function an(v){let s=String(v||'').trim().toLowerCase();return s.startsWith('/')?s:'/'+s}
function mkdir(){try{fs.mkdirSync(DIR,{recursive:true})}catch(e){console.error('[DB] mkdir',e.message)}}
function prune(){const cut=Date.now()-RETAIN;db.listings=db.listings.filter(x=>Number(x.lastSeen||0)>=cut);db.listings.sort((a,b)=>b.lastSeen-a.lastSeen);if(db.listings.length>50000)db.listings.length=50000}
function load(){
  mkdir();
  try{
    if(fs.existsSync(FILE)){
      const x=JSON.parse(fs.readFileSync(FILE,'utf8'));
      if(x&&Array.isArray(x.listings)) db=x;
    }
  }catch(e){console.error('[DB] load',e.message)}
  if(!db||typeof db!=='object')db={version:3,listings:[],wallets:{}};
  if(!Array.isArray(db.listings))db.listings=[];
  if(!db.wallets||typeof db.wallets!=='object'||Array.isArray(db.wallets))db.wallets={};

  if(Number(db.version||0)<3){
    for(const wallet of Object.values(db.wallets)){
      if(wallet&&typeof wallet==='object') wallet.balance=0;
    }
  }

  db.version=3;
  prune();
  save();
  console.log('[DB] loaded listings='+db.listings.length);
  console.log('[DB] sample names:', db.listings.slice(0,25).map(x=>x.name).join(' | '));
}
function save(){mkdir();try{const t=FILE+'.tmp';fs.writeFileSync(t,JSON.stringify(db));fs.renameSync(t,FILE)}catch(e){console.error('[DB] save',e.message)}}
function later(){if(saveTimer)return;saveTimer=setTimeout(()=>{saveTimer=null;save()},400)}
function parsePrice(rawValue){
  let s=strip(rawValue);
  if(!s)return null;

  s=s
    .replace(/\\\\n/g,' ')
    .replace(/\\n/g,' ')
    .replace(/[{}\[\]"']/g,' ')
    .replace(/_/g,' ')
    .replace(/\s+/g,' ');

  const marker='(?:цена|стоимость|price|за\\s*штуку|монет(?:а|ы)?|coins?|коин(?:а|ов|ы)?)';
  const patterns=[
    new RegExp(marker+'[^0-9]{0,80}([0-9][0-9\\s.,]*)(?:\\s*)(к|k|тыс|м|m|млн)?','iu'),
    new RegExp('([0-9][0-9\\s.,]*)(?:\\s*)(к|k|тыс|м|m|млн)?[^0-9]{0,50}'+marker,'iu'),
    /[$₽]\s*([0-9][0-9\s.,]*)(?:\s*)(к|k|тыс|м|m|млн)?/iu
  ];

  for(const re of patterns){
    const m=s.match(re);
    if(!m)continue;

    let number=String(m[1]||'').replace(/\s/g,'').trim();
    const suffix=String(m[2]||'').toLowerCase();

    let multiplier=1;
    if(['к','k','тыс'].includes(suffix))multiplier=1000;
    if(['м','m','млн'].includes(suffix))multiplier=1000000;

    const seps=(number.match(/[.,]/g)||[]).length;
    if(seps>1 || /[.,]\d{3}(?:[.,]\d{3})*$/.test(number)){
      number=number.replace(/[.,]/g,'');
    }else{
      number=number.replace(',','.');
    }

    const n=Number(number);
    const value=Math.round(n*multiplier);
    if(Number.isFinite(value)&&value>0&&value<=1e15)return value;
  }
  return null;
}
function clean(r){
  const name=strip(r?.name).slice(0,160),
        rawText=strip(r?.rawText||'').slice(0,6000),
        supplied=Math.round(Number(r?.price||0)),
        parsed=parsePrice(rawText||name),
        price=(Number.isFinite(supplied)&&supplied>0)?supplied:parsed,
        count=Math.max(1,Math.min(9999,Math.round(Number(r?.count||1)))),
        slot=Math.max(-1,Math.min(9999,Math.round(Number(r?.slot??-1)))),
        fingerprint=String(r?.fingerprint||'').trim().slice(0,128);

  if(!name||!Number.isFinite(price)||price<=0||price>1e15||!/^[a-f0-9]{16,128}$/i.test(fingerprint))return null;
  return{name,normalizedName:norm(name),price,count,slot,fingerprint};
}
function upsert(collector,auction,row,title,now){
  const key=auction+'|'+row.fingerprint,old=db.listings.find(x=>x.key===key);
  if(old){
    Object.assign(old,row,{lastSeen:now,screenTitle:title});
    old.collectors=Array.from(new Set([...(old.collectors||[]),collector])).slice(-50);
    old.observations=Math.min(1000000,Number(old.observations||1)+1);
    return false;
  }
  db.listings.push({key,auction,...row,screenTitle:title,firstSeen:now,lastSeen:now,collectors:[collector],observations:1});
  return true;
}
function itemMatches(x,q){const n=String(x.normalizedName||'');return n.includes(q)||q.includes(n)}
function summarize(rows,item,requestedAuction,sourceAuction,fallback){
  if(!rows.length)return{ok:true,item,auction:requestedAuction,sourceAuction:null,fallback:false,count:0,average:null,min:null,max:null,collectors:0,updatedAt:null,ageSeconds:null};
  const prices=rows.map(x=>Number(x.price)).filter(Number.isFinite),cs=new Set();
  for(const x of rows)for(const c of x.collectors||[])cs.add(c);
  const updatedAt=Math.max(...rows.map(x=>Number(x.lastSeen||0)));
  return{
    ok:true,item,auction:requestedAuction,sourceAuction,fallback,
    count:prices.length,
    average:Math.round(prices.reduce((a,b)=>a+b,0)/prices.length),
    min:Math.min(...prices),max:Math.max(...prices),
    collectors:cs.size,updatedAt,
    ageSeconds:Math.max(0,Math.round((Date.now()-updatedAt)/1000))
  };
}

app.get('/health',(_q,res)=>{prune();res.json({ok:true,mode:'community-price-database',listings:db.listings.length,wallets:Object.keys(db.wallets).length,freshHours:FRESH/3600000,persistentFile:FILE})});

app.get('/stats',(_q,res)=>{
  prune();
  const c=new Set(),a=new Set();
  for(const x of db.listings){a.add(x.auction);for(const v of x.collectors||[])c.add(v)}
  res.json({ok:true,listings:db.listings.length,collectors:c.size,auctions:[...a].sort(),wallets:Object.keys(db.wallets).length});
});

app.post('/wallet',(req,res)=>{
  const userId=String(req.body?.userId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});

  if(!db.wallets[userId]){
    db.wallets[userId]={
      balance:0,
      createdAt:Date.now()
    };
    later();
  }

  res.json({
    ok:true,
    userId,
    balance:Number(db.wallets[userId].balance||0),
    currency:'Random Coins'
  });
});

app.post('/submit',(req,res)=>{
  const collector=String(req.body?.collector||'').trim().slice(0,80),
        auction=an(req.body?.auction),
        title=strip(req.body?.screenTitle).slice(0,160),
        raw=Array.isArray(req.body?.listings)?req.body.listings.slice(0,120):[];
  if(!/^[a-z0-9_-]{8,80}$/i.test(collector))return res.status(400).json({ok:false,error:'invalid collector id'});
  if(!ALLOWED.test(auction))return res.status(400).json({ok:false,error:'invalid anarchy'});
  if(!raw.length)return res.status(400).json({ok:false,error:'no price listings found'});

  const now=Date.now();let accepted=0,added=0;
  for(const x of raw){
    const r=clean(x);if(!r)continue;
    accepted++;
    if(upsert(collector,auction,r,title,now))added++;
  }
  if(!accepted)return res.status(400).json({ok:false,error:'no valid price listings found'});
  prune();later();
  console.log('[SUBMIT]', auction, collector.slice(0,8), 'raw='+raw.length, 'accepted='+accepted, 'added='+added);
  res.json({ok:true,auction,accepted,added,databaseSize:db.listings.length});
});

app.post('/price',(req,res)=>{
  const item=strip(req.body?.item),auction=an(req.body?.auction);
  if(!item||!ALLOWED.test(auction))return res.status(400).json({ok:false,error:'item and valid auction are required'});

  prune();
  const q=norm(item),freshCut=Date.now()-FRESH;
  const all=db.listings.filter(x=>itemMatches(x,q));

  const exactFresh=all.filter(x=>x.auction===auction&&x.lastSeen>=freshCut);
  if(exactFresh.length)return res.json({...summarize(exactFresh,item,auction,auction,false),stale:false});

  const exactAny=all.filter(x=>x.auction===auction);
  if(exactAny.length)return res.json({...summarize(exactAny,item,auction,auction,false),stale:true});

  const freshOther=all.filter(x=>x.auction!==auction&&x.lastSeen>=freshCut);
  const pool=freshOther.length?freshOther:all.filter(x=>x.auction!==auction);
  const stale=!freshOther.length;

  const byAuction=new Map();
  for(const row of pool){
    if(!byAuction.has(row.auction))byAuction.set(row.auction,[]);
    byAuction.get(row.auction).push(row);
  }

  let bestAuction=null,bestRows=[],bestSeen=-1;
  for(const [source,rows] of byAuction){
    const seen=Math.max(...rows.map(x=>Number(x.lastSeen||0)));
    if(seen>bestSeen){bestSeen=seen;bestAuction=source;bestRows=rows}
  }

  if(bestRows.length)return res.json({...summarize(bestRows,item,auction,bestAuction,true),stale});
  return res.json({...summarize([],item,auction,null,false),stale:false});
});

process.on('SIGTERM',()=>{save();process.exit(0)});
process.on('SIGINT',()=>{save();process.exit(0)});
load();
app.listen(PORT,'0.0.0.0',()=>console.log('[HTTP] community price database',PORT));
