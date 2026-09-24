const express=require('express'),fs=require('fs'),path=require('path');
const app=express(); app.use(express.json({limit:'512kb'}));

const PORT=Number(process.env.PORT||3000), DIR=process.env.DATA_DIR||'/data';
const SHOP_API_KEY=String(process.env.SHOP_API_KEY||'');
const SHOP=Object.freeze({
  plus:{id:'plus',name:'Plus',price:1000,category:'main'},
  premium:{id:'premium',name:'Premium',price:5000,category:'main'},

  name_color:{id:'name_color',name:'🎨 Цвет ника',price:500,category:'items'},
  crown:{id:'crown',name:'👑 Корона возле имени',price:1500,category:'items'},
  star_badge:{id:'star_badge',name:'⭐ Значок возле ника',price:800,category:'items'},
  profile_frame:{id:'profile_frame',name:'🖼 Рамка профиля',price:1000,category:'items'},
  message_style:{id:'message_style',name:'💬 Особый стиль сообщений',price:700,category:'items'},
  random_item:{id:'random_item',name:'🎁 Случайный предмет',price:300,category:'items'},
  rnmd_badge:{id:'rnmd_badge',name:'🔥 Редкий значок RNMD',price:2000,category:'items'},
  diamond_badge:{id:'diamond_badge',name:'💎 Алмазный значок',price:2500,category:'items'},
  sakura_badge:{id:'sakura_badge',name:'🌸 Sakura-значок',price:1200,category:'items'},
  trophy:{id:'trophy',name:'🏆 Коллекционный трофей',price:3000,category:'items'},

  premium_gold_frame:{id:'premium_gold_frame',name:'👑 Золотая Premium-рамка',price:2200,category:'items',premiumOnly:true},
  premium_star:{id:'premium_star',name:'🌟 Premium-звезда',price:1600,category:'items',premiumOnly:true},
  autumn_frame:{id:'autumn_frame',name:'🍂 Осенняя рамка',price:1800,category:'items',availableUntil:'2026-10-31T23:59:59Z'},
  pumpkin_badge:{id:'pumpkin_badge',name:'🎃 Тыквенный значок',price:1200,category:'items',availableUntil:'2026-11-02T23:59:59Z'}
});
const PROFILE_COLORS=Object.freeze({
  green:{id:'green',name:'Зелёный'},
  white:{id:'white',name:'Белый'},
  gray:{id:'gray',name:'Серый'},
  black:{id:'black',name:'Чёрный'},
  red:{id:'red',name:'Красный'},
  purple:{id:'purple',name:'Фиолетовый'},
  pink:{id:'pink',name:'Розовый'},
  dark_green:{id:'dark_green',name:'Тёмно-зелёный'},
  light_blue:{id:'light_blue',name:'Голубой'},
  blue:{id:'blue',name:'Синий'}
});
const CASE_COST=400;
const TITLES=Object.freeze({
  newbie:{id:'newbie',name:'Новичок',level:1},
  active:{id:'active',name:'Активист',level:3},
  collector:{id:'collector',name:'Коллекционер',level:5},
  veteran:{id:'veteran',name:'Ветеран',level:10},
  vip:{id:'vip',name:'VIP',requires:'plus'},
  premium:{id:'premium',name:'Premium',requires:'premium'},
  rnmd:{id:'rnmd',name:'RNMD',requires:'rnmd_badge'}
});
const FILE=path.join(DIR,'spooky-prices.json');
const FRESH=Number(process.env.PRICE_FRESH_MS||7200000), RETAIN=Number(process.env.PRICE_RETAIN_MS||259200000);
const ALLOWED=/^\/an(?:10[1-8]|20[1-9]|30[1-9])$/i;

let db={version:3,listings:[],wallets:{},promocodes:{},customShop:{},settings:{}},saveTimer=null;

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
  if(!db.promocodes||typeof db.promocodes!=='object'||Array.isArray(db.promocodes))db.promocodes={};
  if(!db.customShop||typeof db.customShop!=='object'||Array.isArray(db.customShop))db.customShop={};
  if(!db.settings||typeof db.settings!=='object'||Array.isArray(db.settings))db.settings={};
  if(!db.settings.daily||typeof db.settings.daily!=='object'){
    db.settings.daily={coins:250,itemId:null,streakBonus:true};
  }
  if(!db.settings.dailySchedule||typeof db.settings.dailySchedule!=='object'||Array.isArray(db.settings.dailySchedule)){
    db.settings.dailySchedule={};
  }
  for(const wallet of Object.values(db.wallets)){
    if(wallet&&typeof wallet==='object'&&(!wallet.purchases||typeof wallet.purchases!=='object'||Array.isArray(wallet.purchases))){
      wallet.purchases={};
    }
    if(wallet&&typeof wallet==='object'&&(!wallet.decorations||typeof wallet.decorations!=='object'||Array.isArray(wallet.decorations))){
      wallet.decorations={};
      for(const itemId of Object.keys(wallet.purchases||{})){
        if(getShopItem(itemId)?.category==='items')wallet.decorations[itemId]=true;
      }
    }
    if(wallet&&typeof wallet==='object'&&!PROFILE_COLORS[wallet.nameColor]){
      wallet.nameColor='white';
    }
    if(wallet&&typeof wallet==='object'){
      if(!wallet.likesBy||typeof wallet.likesBy!=='object'||Array.isArray(wallet.likesBy))wallet.likesBy={};
      if(!wallet.titleId)wallet.titleId='newbie';
      if(!Number.isFinite(Number(wallet.xp)))wallet.xp=0;
      if(!Number.isFinite(Number(wallet.dailyStreak)))wallet.dailyStreak=0;
      ensureStats(wallet);
    }
  }

  if(Number(db.version||0)<3){
    for(const wallet of Object.values(db.wallets)){
      if(wallet&&typeof wallet==='object') wallet.balance=0;
    }
  }

  db.version=3;
  db.listings=db.listings.filter(x=>!(String(x.normalizedName||'').includes('тотем') && Number(x.price)===3));
  prune();
  save();
  console.log('[DB] loaded listings='+db.listings.length);
  console.log('[DB] sample names:', db.listings.slice(0,25).map(x=>x.name).join(' | '));
}
function save(){mkdir();try{const t=FILE+'.tmp';fs.writeFileSync(t,JSON.stringify(db));fs.renameSync(t,FILE)}catch(e){console.error('[DB] save',e.message)}}
function later(){if(saveTimer)return;saveTimer=setTimeout(()=>{saveTimer=null;save()},400)}
function parseNumericPrice(number,suffix){
  let n=String(number||'').replace(/\s/g,'').trim();
  const unit=String(suffix||'').toLowerCase();
  if(!n)return null;

  const seps=(n.match(/[.,]/g)||[]).length;
  if(seps>1 || /[.,]\d{3}(?:[.,]\d{3})*$/.test(n)){
    n=n.replace(/[.,]/g,'');
  }else{
    n=n.replace(',','.');
  }

  let multiplier=1;
  if(['к','k','тыс'].includes(unit))multiplier=1000;
  if(['м','m','млн'].includes(unit))multiplier=1000000;

  const base=Number(n);
  const value=Math.round(base*multiplier);
  return Number.isFinite(value)&&value>0&&value<=1e15?value:null;
}

function parsePrice(rawValue){
  let s=strip(rawValue);
  if(!s)return null;

  s=s
    .replace(/\\\\n/g,'\n')
    .replace(/\\n/g,'\n')
    .replace(/§[0-9A-FK-OR]/gi,'');

  const lines=s
    .split(/\r?\n/)
    .map(x=>x.replace(/[{}\[\]"']/g,' ').replace(/_/g,' ').replace(/\s+/g,' ').trim())
    .filter(Boolean);

  const marker=/(?:цена|стоимость|price|за\s*штуку|купить|продажа|монет(?:а|ы)?|coins?|коин(?:а|ов|ы)?)/iu;
  const currency=/[$₽]/u;
  const numberRe=/([0-9][0-9\s.,]*?)(?:\s*)(к|k|тыс|м|m|млн)?(?=\s|$|[$₽])/giu;

  for(const line of lines){
    if(!marker.test(line) && !currency.test(line))continue;

    const values=[];
    numberRe.lastIndex=0;
    let m;
    while((m=numberRe.exec(line))!==null){
      const value=parseNumericPrice(m[1],m[2]);
      if(value!==null)values.push(value);
    }

    if(values.length)return Math.max(...values);
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

function levelFromXp(xp){return Math.max(1,Math.floor(Number(xp||0)/100)+1)}
function isItemAvailable(item){
  if(!item)return false;
  if(item.availableUntil && Date.now()>Date.parse(item.availableUntil))return false;
  return true;
}
function allShopMap(){return {...SHOP,...(db.customShop||{})}}
function allShopItems(){return Object.values(allShopMap())}
function getShopItem(id){return SHOP[id]||db.customShop?.[id]||null}

function itemAccessAllowed(wallet,item){
  if(!isItemAvailable(item))return {ok:false,code:'expired'};
  if(item.dailyOnly)return {ok:false,code:'daily_only'};
  if(item.premiumOnly && !wallet.purchases?.premium)return {ok:false,code:'premium_required'};
  return {ok:true};
}
function ensureStats(wallet){
  if(!wallet.stats||typeof wallet.stats!=='object'||Array.isArray(wallet.stats))wallet.stats={};
  const keys=['messages','purchases','spent','received','transferred','giftsSent','giftsReceived','casesOpened','dailyClaims'];
  for(const k of keys)wallet.stats[k]=Math.max(0,Number(wallet.stats[k]||0));
}
function touchIdentity(wallet,raw){
  if(raw?.displayName)wallet.displayName=strip(raw.displayName).slice(0,100);
  if(raw?.username)wallet.username=strip(raw.username).replace(/^@/,'').slice(0,64);
}
function addXp(wallet,amount){
  wallet.xp=Math.max(0,Number(wallet.xp||0)+Math.max(0,Math.round(Number(amount||0))));
  return levelFromXp(wallet.xp);
}
function unlockedTitles(wallet){
  const level=levelFromXp(wallet.xp);
  return Object.values(TITLES).filter(t=>{
    if(t.level && level<t.level)return false;
    if(t.requires==='plus'&&!wallet.purchases?.plus)return false;
    if(t.requires==='premium'&&!wallet.purchases?.premium)return false;
    if(t.requires==='rnmd_badge'&&!wallet.purchases?.rnmd_badge)return false;
    return true;
  });
}
function collectionCount(wallet){
  return Object.keys(wallet.purchases||{}).filter(id=>getShopItem(id)?.category==='items').length;
}
function publicWallet(userId,wallet){
  ensureStats(wallet);
  const titles=unlockedTitles(wallet);
  if(!titles.some(t=>t.id===wallet.titleId))wallet.titleId=titles[0]?.id||'newbie';
  return{
    userId,
    displayName:wallet.displayName||null,
    username:wallet.username||null,
    balance:Number(wallet.balance||0),
    xp:Number(wallet.xp||0),
    level:levelFromXp(wallet.xp),
    titleId:wallet.titleId,
    title:titles.find(t=>t.id===wallet.titleId)?.name||'Новичок',
    likes:Object.keys(wallet.likesBy||{}).length,
    collection:collectionCount(wallet),
    streak:Number(wallet.dailyStreak||0),
    favoriteDecoration:wallet.favoriteDecoration||null,
    stats:{...wallet.stats}
  };
}

app.get('/health',(_q,res)=>{prune();res.json({ok:true,mode:'community-price-database',listings:db.listings.length,wallets:Object.keys(db.wallets).length,freshHours:FRESH/3600000,persistentFile:FILE})});

app.get('/stats',(_q,res)=>{
  prune();
  const c=new Set(),a=new Set();
  for(const x of db.listings){a.add(x.auction);for(const v of x.collectors||[])c.add(v)}
  res.json({ok:true,listings:db.listings.length,collectors:c.size,auctions:[...a].sort(),wallets:Object.keys(db.wallets).length});
});

function getWallet(userId){
  if(!db.wallets[userId]){
    db.wallets[userId]={
      balance:0,createdAt:Date.now(),purchases:{},decorations:{},nameColor:'white',
      xp:0,titleId:'newbie',likesBy:{},dailyStreak:0,lastDailyAt:0,
      favoriteDecoration:null,stats:{}
    };
  }
  const wallet=db.wallets[userId];
  if(!wallet.purchases||typeof wallet.purchases!=='object')wallet.purchases={};
  if(!wallet.decorations||typeof wallet.decorations!=='object'||Array.isArray(wallet.decorations)){
    wallet.decorations={};
    for(const itemId of Object.keys(wallet.purchases)){
      if(getShopItem(itemId)?.category==='items')wallet.decorations[itemId]=true;
    }
  }
  if(!PROFILE_COLORS[wallet.nameColor])wallet.nameColor='white';
  if(!wallet.likesBy||typeof wallet.likesBy!=='object'||Array.isArray(wallet.likesBy))wallet.likesBy={};
  if(!wallet.titleId)wallet.titleId='newbie';
  if(!Number.isFinite(Number(wallet.xp)))wallet.xp=0;
  if(!Number.isFinite(Number(wallet.dailyStreak)))wallet.dailyStreak=0;
  ensureStats(wallet);
  return wallet;
}

function shopAuthorized(req){
  return Boolean(SHOP_API_KEY) && req.get('x-shop-key')===SHOP_API_KEY;
}

app.post('/wallet',(req,res)=>{
  const userId=String(req.body?.userId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});

  const wallet=getWallet(userId);
  later();

  res.json({
    ok:true,
    userId,
    balance:Number(wallet.balance||0),
    currency:'Random Coins',
    purchases:Object.keys(wallet.purchases||{})
  });
});

app.post('/shop',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});

  const wallet=getWallet(userId);
  later();

  const items=allShopItems()
    .filter(item=>wallet.purchases?.[item.id] || (!item.dailyOnly && isItemAvailable(item)))
    .map(item=>({
      ...item,
      owned:Boolean(wallet.purchases?.[item.id]),
      locked:Boolean(item.premiumOnly&&!wallet.purchases?.premium)
    }));

  res.json({
    ok:true,
    balance:Number(wallet.balance||0),
    currency:'Random Coins',
    items
  });
});

app.post('/buy',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  const itemId=String(req.body?.itemId??'').trim().toLowerCase();

  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  const item=getShopItem(itemId);
  if(!item)return res.status(400).json({ok:false,error:'invalid item'});

  const wallet=getWallet(userId);
  const access=itemAccessAllowed(wallet,item);
  if(!access.ok)return res.status(403).json({ok:false,code:access.code,error:access.code,item});
  const balance=Number(wallet.balance||0);

  if(wallet.purchases?.[item.id]){
    return res.status(409).json({
      ok:false,
      code:'already_owned',
      error:'already owned',
      item,
      balance
    });
  }

  if(balance<item.price){
    return res.status(400).json({
      ok:false,
      code:'insufficient_funds',
      error:'insufficient funds',
      item,
      balance,
      missing:item.price-balance
    });
  }

  wallet.balance=balance-item.price;
  wallet.stats.spent+=item.price;
  wallet.stats.purchases+=1;
  addXp(wallet,25);
  wallet.purchases[item.id]={
    name:item.name,
    price:item.price,
    purchasedAt:Date.now()
  };
  if(item.category==='items'){
    wallet.decorations[item.id]=true;
  }
  if(item.id==='name_color'&&!PROFILE_COLORS[wallet.nameColor]){
    wallet.nameColor='white';
  }
  save();

  res.json({
    ok:true,
    item,
    balance:wallet.balance,
    purchase:wallet.purchases[item.id]
  });
});

app.post('/profile',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});

  const wallet=getWallet(userId);
  later();

  const purchases=Object.keys(wallet.purchases||{});
  const cosmetics=allShopItems()
    .filter(item=>item.category==='items'&&wallet.purchases?.[item.id])
    .map(item=>({
      ...item,
      equipped:wallet.decorations?.[item.id]!==false
    }));

  res.json({
    ok:true,
    userId,
    balance:Number(wallet.balance||0),
    plus:Boolean(wallet.purchases?.plus),
    premium:Boolean(wallet.purchases?.premium),
    purchases,
    cosmetics,
    nameColor:wallet.nameColor||'white',
    availableColors:Object.values(PROFILE_COLORS),
    ...publicWallet(userId,wallet),
    unlockedTitles:unlockedTitles(wallet),
    favoriteDecoration:wallet.favoriteDecoration||null
  });
});

app.post('/profile/decorate',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  const itemId=String(req.body?.itemId??'').trim().toLowerCase();

  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});

  const item=getShopItem(itemId);
  if(!item||item.category!=='items')return res.status(400).json({ok:false,error:'invalid decoration'});

  const wallet=getWallet(userId);
  if(!wallet.purchases?.[itemId]){
    return res.status(403).json({ok:false,error:'decoration not owned'});
  }

  const enabled=wallet.decorations?.[itemId]!==false;
  wallet.decorations[itemId]=!enabled;
  save();

  res.json({
    ok:true,
    itemId,
    equipped:wallet.decorations[itemId]
  });
});

app.post('/profile/color',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  const colorId=String(req.body?.colorId??'').trim().toLowerCase();

  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  if(!PROFILE_COLORS[colorId])return res.status(400).json({ok:false,error:'invalid color'});

  const wallet=getWallet(userId);
  if(!wallet.purchases?.name_color){
    return res.status(403).json({ok:false,error:'name color not owned'});
  }

  wallet.nameColor=colorId;
  save();

  res.json({
    ok:true,
    nameColor:colorId,
    color:PROFILE_COLORS[colorId]
  });
});

app.post('/activity',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  const wallet=getWallet(userId);
  touchIdentity(wallet,req.body);
  const kind=String(req.body?.kind||'message');
  if(kind==='message'){wallet.stats.messages+=1;addXp(wallet,5)}
  else addXp(wallet,1);
  later();
  res.json({ok:true,...publicWallet(userId,wallet)});
});

app.post('/daily',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  const wallet=getWallet(userId);
  touchIdentity(wallet,req.body);

  const now=Date.now(),last=Number(wallet.lastDailyAt||0),cooldown=24*60*60*1000;
  if(last&&now-last<cooldown){
    return res.status(429).json({ok:false,code:'daily_cooldown',remainingMs:cooldown-(now-last),streak:Number(wallet.dailyStreak||0)});
  }

  if(last&&now-last<=48*60*60*1000)wallet.dailyStreak=Math.max(1,Number(wallet.dailyStreak||0)+1);
  else wallet.dailyStreak=1;
  wallet.lastDailyAt=now;

  const schedule=db.settings?.dailySchedule||{};
  const hasSchedule=Object.keys(schedule).length>0;
  const cfg=schedule[String(wallet.dailyStreak)]
    || (hasSchedule
      ? {coins:0,itemId:null,streakBonus:false}
      : (db.settings?.daily||{coins:250,itemId:null,streakBonus:true}));
  const baseCoins=Math.max(0,Math.round(Number(cfg.coins||0)));
  const milestone=cfg.streakBonus===false?0:({3:150,7:500,14:1200,30:3000}[wallet.dailyStreak]||0);
  const reward=baseCoins+milestone;

  if(reward>0){
    wallet.balance=Number(wallet.balance||0)+reward;
    wallet.stats.received+=reward;
  }

  let rewardItem=null;
  let itemAlreadyOwned=false;
  if(cfg.itemId){
    const item=getShopItem(String(cfg.itemId));
    if(item&&isItemAvailable(item)){
      if(wallet.purchases?.[item.id]){
        itemAlreadyOwned=true;
      }else{
        wallet.purchases[item.id]={name:item.name,price:0,purchasedAt:Date.now(),source:'daily'};
        if(item.category==='items')wallet.decorations[item.id]=true;
        rewardItem=item;
      }
    }
  }

  wallet.stats.dailyClaims+=1;
  addXp(wallet,20);
  save();

  res.json({
    ok:true,
    reward,
    baseCoins,
    milestone,
    rewardItem,
    itemAlreadyOwned,
    streak:wallet.dailyStreak,
    balance:wallet.balance,
    level:levelFromXp(wallet.xp)
  });
});

app.post('/transfer',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const fromId=String(req.body?.fromUserId??'').trim(),toId=String(req.body?.toUserId??'').trim();
  const amount=Math.round(Number(req.body?.amount));
  if(!/^-?\d{1,20}$/.test(fromId)||!/^-?\d{1,20}$/.test(toId))return res.status(400).json({ok:false,error:'invalid user id'});
  if(fromId===toId)return res.status(400).json({ok:false,code:'self_transfer',error:'self transfer'});
  if(!Number.isFinite(amount)||amount<1||amount>1000000000)return res.status(400).json({ok:false,error:'invalid amount'});
  const from=getWallet(fromId),to=getWallet(toId);
  if(Number(from.balance||0)<amount)return res.status(400).json({ok:false,code:'insufficient_funds',missing:amount-Number(from.balance||0)});
  from.balance-=amount; to.balance=Number(to.balance||0)+amount;
  from.stats.transferred+=amount; to.stats.received+=amount;
  addXp(from,5);
  save();
  res.json({ok:true,amount,fromBalance:from.balance,toBalance:to.balance});
});

app.post('/like',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const fromId=String(req.body?.fromUserId??'').trim(),toId=String(req.body?.toUserId??'').trim();
  if(!/^-?\d{1,20}$/.test(fromId)||!/^-?\d{1,20}$/.test(toId))return res.status(400).json({ok:false,error:'invalid user id'});
  if(fromId===toId)return res.status(400).json({ok:false,code:'self_like'});
  const target=getWallet(toId);
  if(target.likesBy[fromId])return res.status(409).json({ok:false,code:'already_liked',likes:Object.keys(target.likesBy).length});
  target.likesBy[fromId]=Date.now();
  addXp(target,2);
  save();
  res.json({ok:true,likes:Object.keys(target.likesBy).length});
});

app.post('/case/open',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  const wallet=getWallet(userId);
  if(Number(wallet.balance||0)<CASE_COST)return res.status(400).json({ok:false,code:'insufficient_funds',missing:CASE_COST-Number(wallet.balance||0)});
  wallet.balance-=CASE_COST;wallet.stats.spent+=CASE_COST;wallet.stats.casesOpened+=1;addXp(wallet,10);
  const available=allShopItems().filter(item=>item.category==='items'&&isItemAvailable(item)&&!item.premiumOnly&&!item.dailyOnly&&!wallet.purchases?.[item.id]);
  let reward;
  if(available.length&&Math.random()<0.25){
    const item=available[Math.floor(Math.random()*available.length)];
    wallet.purchases[item.id]={name:item.name,price:0,purchasedAt:Date.now(),source:'case'};
    wallet.decorations[item.id]=true;
    reward={type:'item',item};
  }else{
    const amount=[150,200,250,300,500,750,1000][Math.floor(Math.random()*7)];
    wallet.balance+=amount;wallet.stats.received+=amount;
    reward={type:'coins',amount};
  }
  save();
  res.json({ok:true,cost:CASE_COST,reward,balance:wallet.balance});
});

app.post('/profile/title',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim(),titleId=String(req.body?.titleId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  const wallet=getWallet(userId),titles=unlockedTitles(wallet);
  if(!titles.some(t=>t.id===titleId))return res.status(403).json({ok:false,error:'title locked'});
  wallet.titleId=titleId;save();
  res.json({ok:true,titleId,title:titles.find(t=>t.id===titleId)});
});

app.post('/profile/favorite',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim(),itemId=String(req.body?.itemId??'').trim();
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  const wallet=getWallet(userId),item=getShopItem(itemId);
  if(!item||item.category!=='items'||!wallet.purchases?.[itemId])return res.status(403).json({ok:false,error:'not owned'});
  wallet.favoriteDecoration=itemId;save();
  res.json({ok:true,itemId});
});

app.post('/leaderboard',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const type=String(req.body?.type||'level');
  const rows=Object.entries(db.wallets).map(([userId,w])=>({userId,...publicWallet(userId,getWallet(userId))}));
  const key=type==='coins'?'balance':(type==='collection'?'collection':'level');
  rows.sort((a,b)=>Number(b[key]||0)-Number(a[key]||0)||Number(b.xp||0)-Number(a.xp||0));
  res.json({ok:true,type,rows:rows.slice(0,10)});
});

app.post('/admin/daily',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const coins=Math.max(0,Math.min(1000000000,Math.round(Number(req.body?.coins||0))));
  const rawItem=String(req.body?.itemId||'').trim().toLowerCase();
  const itemId=rawItem?rawItem:null;
  const streakBonus=req.body?.streakBonus!==false;
  const day=Math.round(Number(req.body?.day||1));

  if(!Number.isFinite(day)||day<1||day>3650)return res.status(400).json({ok:false,error:'invalid day'});
  if(itemId&&!getShopItem(itemId))return res.status(400).json({ok:false,error:'invalid item'});
  if(coins===0&&!itemId)return res.status(400).json({ok:false,error:'reward required'});

  if(!db.settings.dailySchedule||typeof db.settings.dailySchedule!=='object'||Array.isArray(db.settings.dailySchedule)){
    db.settings.dailySchedule={};
  }

  const daily={coins,itemId,streakBonus};
  db.settings.dailySchedule[String(day)]=daily;
  save();
  res.json({ok:true,day,daily,item:itemId?getShopItem(itemId):null});
});

app.post('/admin/daily/get',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const daily=db.settings?.daily||{coins:250,itemId:null,streakBonus:true};
  const scheduleObj=db.settings?.dailySchedule||{};
  const schedule=Object.entries(scheduleObj)
    .map(([day,cfg])=>({
      day:Number(day),
      coins:Number(cfg?.coins||0),
      itemId:cfg?.itemId||null,
      streakBonus:cfg?.streakBonus!==false,
      item:cfg?.itemId?getShopItem(cfg.itemId):null
    }))
    .filter(x=>Number.isFinite(x.day)&&x.day>=1)
    .sort((a,b)=>a.day-b.day);
  res.json({ok:true,daily,item:daily.itemId?getShopItem(daily.itemId):null,schedule});
});

app.post('/admin/promos',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const promos=Object.values(db.promocodes||{}).map(p=>({
    code:p.code,
    amount:Number(p.amount||0),
    itemId:p.itemId||null,
    maxUses:Number(p.maxUses||0),
    uses:Object.keys(p.usedBy||{}).length,
    createdAt:p.createdAt||null
  })).sort((a,b)=>Number(b.createdAt||0)-Number(a.createdAt||0));
  res.json({ok:true,promos});
});

app.post('/admin/promo/delete',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const code=String(req.body?.code||'').trim().toUpperCase().replace(/\s+/g,'');
  if(!db.promocodes?.[code])return res.status(404).json({ok:false,code:'promo_not_found'});
  delete db.promocodes[code];
  save();
  res.json({ok:true,code});
});

app.post('/admin/exclusive',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});

  const name=strip(req.body?.name).slice(0,60);
  const emoji=strip(req.body?.emoji||'✨').slice(0,8);
  const dailyOnly=Boolean(req.body?.dailyOnly);
  const rawPrice=Math.round(Number(req.body?.price||0));
  const price=dailyOnly?0:Math.max(1,Math.min(1000000000,rawPrice));
  const premiumOnly=dailyOnly?false:Boolean(req.body?.premiumOnly);
  const days=Math.max(0,Math.min(3650,Math.round(Number(req.body?.days||0))));

  if(!name)return res.status(400).json({ok:false,error:'name required'});
  if(!dailyOnly&&!price)return res.status(400).json({ok:false,error:'price required'});

  let id;
  do{id='ex_'+Date.now().toString(36)+Math.floor(Math.random()*1296).toString(36).padStart(2,'0')}while(db.customShop[id]);

  const item={
    id,
    name:(emoji?emoji+' ':'')+name,
    price,
    category:'items',
    customExclusive:true,
    dailyOnly,
    premiumOnly,
    createdAt:Date.now()
  };
  if(days>0)item.availableUntil=new Date(Date.now()+days*86400000).toISOString();

  db.customShop[id]=item;
  save();
  res.json({ok:true,item});
});

app.post('/admin/promo',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const code=String(req.body?.code||'').trim().toUpperCase().replace(/\s+/g,'');
  const amount=Math.max(0,Math.round(Number(req.body?.amount||0)));
  const itemId=String(req.body?.itemId||'').trim().toLowerCase();
  const maxUses=Math.max(1,Math.min(100000,Math.round(Number(req.body?.maxUses||100))));
  if(!/^[A-Z0-9_-]{3,24}$/.test(code))return res.status(400).json({ok:false,error:'invalid code'});
  const promoItem=getShopItem(itemId);
  if(!amount&&!promoItem)return res.status(400).json({ok:false,error:'reward required'});
  if(promoItem?.dailyOnly)return res.status(400).json({ok:false,code:'daily_only_item',error:'daily-only item cannot be used in promo'});
  db.promocodes[code]={code,amount,itemId:promoItem?itemId:null,maxUses,usedBy:{},createdAt:Date.now()};
  save();
  res.json({ok:true,promo:db.promocodes[code]});
});

app.post('/promo/redeem',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim(),code=String(req.body?.code||'').trim().toUpperCase().replace(/\s+/g,'');
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  const promo=db.promocodes?.[code];
  if(!promo)return res.status(404).json({ok:false,code:'promo_not_found'});
  if(promo.usedBy?.[userId])return res.status(409).json({ok:false,code:'promo_used'});
  if(Object.keys(promo.usedBy||{}).length>=Number(promo.maxUses||0))return res.status(410).json({ok:false,code:'promo_limit'});
  const wallet=getWallet(userId);
  let reward={};
  if(promo.amount){
    wallet.balance=Number(wallet.balance||0)+promo.amount;wallet.stats.received+=promo.amount;
    reward.amount=promo.amount;
  }
  if(promo.itemId&&getShopItem(promo.itemId)&&!wallet.purchases?.[promo.itemId]){
    const item=getShopItem(promo.itemId);
    wallet.purchases[promo.itemId]={name:item.name,price:0,purchasedAt:Date.now(),source:'promo'};
    if(item.category==='items')wallet.decorations[promo.itemId]=true;
    reward.item=item;
  }
  if(!promo.usedBy||typeof promo.usedBy!=='object')promo.usedBy={};
  promo.usedBy[userId]=Date.now();addXp(wallet,10);save();
  res.json({ok:true,reward,balance:wallet.balance});
});

app.post('/gift/buy',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const fromId=String(req.body?.fromUserId??'').trim(),toId=String(req.body?.toUserId??'').trim(),itemId=String(req.body?.itemId??'').trim().toLowerCase();
  if(!/^-?\d{1,20}$/.test(fromId)||!/^-?\d{1,20}$/.test(toId))return res.status(400).json({ok:false,error:'invalid user id'});
  if(fromId===toId)return res.status(400).json({ok:false,code:'self_gift'});
  const item=getShopItem(itemId);if(!item||item.category!=='items')return res.status(400).json({ok:false,error:'invalid item'});
  if(item.dailyOnly)return res.status(403).json({ok:false,code:'daily_only'});
  const from=getWallet(fromId),to=getWallet(toId);
  if(!isItemAvailable(item))return res.status(403).json({ok:false,code:'expired'});
  if(item.premiumOnly&&!to.purchases?.premium)return res.status(403).json({ok:false,code:'recipient_premium_required'});
  if(to.purchases?.[itemId])return res.status(409).json({ok:false,code:'already_owned'});
  if(Number(from.balance||0)<item.price)return res.status(400).json({ok:false,code:'insufficient_funds',missing:item.price-Number(from.balance||0)});
  from.balance-=item.price;from.stats.spent+=item.price;from.stats.giftsSent+=1;to.stats.giftsReceived+=1;
  to.purchases[itemId]={name:item.name,price:0,purchasedAt:Date.now(),source:'gift',fromUserId:fromId};to.decorations[itemId]=true;
  addXp(from,15);save();
  res.json({ok:true,item,balance:from.balance});
});

app.post('/admin/coins',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});

  const userId=String(req.body?.userId??'').trim();
  const amount=Math.round(Number(req.body?.amount));

  if(!/^-?\d{1,20}$/.test(userId)){
    return res.status(400).json({ok:false,error:'invalid user id'});
  }

  if(!Number.isFinite(amount)||amount<1||amount>1000000000){
    return res.status(400).json({ok:false,error:'invalid amount'});
  }

  const wallet=getWallet(userId);
  const before=Number(wallet.balance||0);
  wallet.balance=before+amount;
  save();

  res.json({
    ok:true,
    userId,
    amount,
    before,
    balance:wallet.balance
  });
});

app.post('/admin/coins/remove',(req,res)=>{
  if(!shopAuthorized(req))return res.status(401).json({ok:false,error:'unauthorized'});
  const userId=String(req.body?.userId??'').trim();
  const amount=Math.round(Number(req.body?.amount));
  if(!/^-?\d{1,20}$/.test(userId))return res.status(400).json({ok:false,error:'invalid user id'});
  if(!Number.isFinite(amount)||amount<1||amount>1000000000)return res.status(400).json({ok:false,error:'invalid amount'});
  const wallet=getWallet(userId);
  const before=Math.max(0,Number(wallet.balance||0));
  const removed=Math.min(before,amount);
  wallet.balance=before-removed;
  save();
  res.json({ok:true,userId,requested:amount,removed,before,balance:wallet.balance});
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
