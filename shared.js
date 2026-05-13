// ─── CONFIG ────────────────────────────────────────────────────
// Auto-detect backend URL
const API_BASE = (window.location.hostname==='localhost'||window.location.hostname==='127.0.0.1')
  ? 'http://localhost:8000'
  : 'https://serenity-spot-airbnb.up.railway.app';

// ─── ROOMS DATA ────────────────────────────────────────────────
const ROOMS = [
  {
    id:1, type:'Studio', name:'City View Studio',
    price:2500, people:2, rating:4.8, reviews:24,
    badge:'Popular',
    image:'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800&q=80',
    images:[
      'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=900&q=80',
      'https://images.unsplash.com/photo-1540518614846-7eded433c457?w=600&q=80',
      'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=600&q=80',
    ],
    desc:'A compact and stylish studio perfect for solo travelers or couples. Features a queen bed, en-suite bathroom, and sweeping city views.',
    fullDesc:'Enjoy the buzz of the city from your own private retreat. This thoughtfully designed studio includes a queen-size bed, a modern en-suite bathroom with hot shower, a small kitchenette with microwave and kettle, and a workspace for those traveling on business. The large window frames a stunning city panorama, especially beautiful at night.',
    amenities:['WiFi','TV','Kitchen','AC','Hot Water','Workspace'],
    available:true
  },
  {
    id:2, type:'1 Bedroom', name:'Garden Suite',
    price:3800, people:2, rating:4.9, reviews:38,
    badge:'Top Rated',
    image:'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&q=80',
    images:[
      'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=900&q=80',
      'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=600&q=80',
      'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600&q=80',
    ],
    desc:'Spacious one-bedroom with a private bathroom and serene garden view. Perfect for a romantic getaway.',
    fullDesc:'Step into tranquility. The Garden Suite features a large bedroom with a king-size bed, a separate living area with a sofa and smart TV, a fully equipped kitchen, and private garden access. Wake up to birdsong and the scent of fresh flowers every morning.',
    amenities:['WiFi','TV','Full Kitchen','AC','Hot Water','Garden Access','Parking'],
    available:true
  },
  {
    id:3, type:'2 Bedroom', name:'Family Apartment',
    price:5500, people:4, rating:4.7, reviews:19,
    badge:null,
    image:'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&q=80',
    images:[
      'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=900&q=80',
      'https://images.unsplash.com/photo-1560185007-c5ca9d2c014d?w=600&q=80',
      'https://images.unsplash.com/photo-1556909172-54557c7e4fb7?w=600&q=80',
    ],
    desc:'Perfect for families or small groups needing extra space. Two bedrooms, full kitchen, and a comfortable living room.',
    fullDesc:'The Family Apartment is designed for guests who need room to breathe. With two fully furnished bedrooms (one king, one twin), a spacious living room, a full kitchen, two bathrooms, and a private balcony, it offers the comforts of home at a fraction of the cost of a hotel.',
    amenities:['WiFi','2x TV','Full Kitchen','AC','2 Bathrooms','Balcony','Parking','Washer'],
    available:true
  },
  {
    id:4, type:'3 Bedroom', name:'Executive Residence',
    price:8500, people:6, rating:4.9, reviews:11,
    badge:'Best Value',
    image:'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80',
    images:[
      'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=900&q=80',
      'https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=600&q=80',
      'https://images.unsplash.com/photo-1556909172-8c2f041fca1e?w=600&q=80',
    ],
    desc:'Our flagship unit for large families or corporate teams. Three bedrooms, expansive living area, and premium finishes throughout.',
    fullDesc:"The Executive Residence is Serenity Spot's crown jewel. Three ensuite bedrooms (2 kings, 1 twin), an open-plan living and dining area, a chef's kitchen, a private terrace with garden views, and dedicated parking for two vehicles. Ideal for extended stays, family holidays, or executive retreats.",
    amenities:['WiFi','3x TV','Chef Kitchen','AC','3 Bathrooms','Terrace','2x Parking','Washer','Dryer'],
    available:true
  },
];

// ─── SVG ICONS ─────────────────────────────────────────────────
const ICONS = {
  wifi: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1"/></svg>`,
  tv: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="15" rx="2" ry="2"/><polyline points="17 2 12 7 7 2"/></svg>`,
  kitchen: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></svg>`,
  ac: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 16H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-3"/><path d="M12 8v8"/><path d="m9 20 3-3 3 3"/></svg>`,
  shower: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12 L4 5 a 5 5 0 0 1 10 0"/><line x1="4" y1="12" x2="22" y2="12"/><line x1="7" y1="16" x2="7" y2="16"/><line x1="11" y1="16" x2="11" y2="16"/><line x1="15" y1="16" x2="15" y2="16"/><line x1="7" y1="20" x2="7" y2="20"/><line x1="11" y1="20" x2="11" y2="20"/><line x1="15" y1="20" x2="15" y2="20"/></svg>`,
  workspace: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
  garden: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V12"/><path d="M12 12C12 12 8 9 8 5a4 4 0 0 1 8 0c0 4-4 7-4 7z"/><path d="M12 12C12 12 7 10 5 6"/><path d="M12 12C12 12 17 10 19 6"/></svg>`,
  parking: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 17V7h4a3 3 0 0 1 0 6H9"/></svg>`,
  balcony: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
  washer: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="12" cy="13" r="4"/><path d="M7 5h.01M11 5h.01"/></svg>`,
  dryer: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2"/><circle cx="12" cy="13" r="4"/><path d="M7.2 7.2L7 7"/></svg>`,
  star: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  users: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  mappin: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>`,
  phone: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.07 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 2.98 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.09 9.91a16 16 0 0 0 5.93 5.93l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21 16.92z"/></svg>`,
  mail: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`,
  clock: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  check: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
  search: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  arrowRight: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>`,
  shield: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  sparkle: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v1m0 16v1M4.22 4.22l.7.7m12.16 12.16.7.7M3 12h1m16 0h1M4.22 19.78l.7-.7M18.36 5.64l.7-.7"/><circle cx="12" cy="12" r="4"/></svg>`,
  money: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
  globe: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
  verified: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
  whatsapp: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>`,
  facebook: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>`,
  instagram: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>`,
  twitter: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.736-8.842L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>`,
  menu: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`,
  x: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  checkCircle: `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
};

const AMENITY_ICONS = {
  'WiFi': ICONS.wifi,
  'TV': ICONS.tv, '2x TV': ICONS.tv, '3x TV': ICONS.tv,
  'Kitchen': ICONS.kitchen, 'Full Kitchen': ICONS.kitchen, 'Chef Kitchen': ICONS.kitchen,
  'AC': ICONS.ac,
  'Hot Water': ICONS.shower,
  'Workspace': ICONS.workspace,
  'Garden Access': ICONS.garden,
  'Parking': ICONS.parking, '2x Parking': ICONS.parking,
  'Balcony': ICONS.balcony, 'Terrace': ICONS.balcony,
  'Washer': ICONS.washer,
  'Dryer': ICONS.dryer,
  '2 Bathrooms': ICONS.shower, '3 Bathrooms': ICONS.shower,
};

// ─── HELPERS ───────────────────────────────────────────────────
function getRoom(id){ return ROOMS.find(r=>r.id==id); }

function renderStars(rating){
  const full=Math.floor(rating);
  let html='';
  for(let i=0;i<5;i++){
    html+=`<span class="${i<full?'stars':'star-empty'}">${ICONS.star}</span>`;
  }
  return html;
}

function calcNights(checkin,checkout){
  if(!checkin||!checkout) return 0;
  const d1=new Date(checkin),d2=new Date(checkout);
  return Math.max(0,Math.round((d2-d1)/(1000*60*60*24)));
}

function formatKES(n){ return 'KES '+Number(n).toLocaleString(); }

// ─── DARAJA M-PESA API ─────────────────────────────────────────
async function initiateMpesaPayment({phone, amount, accountRef, description}){
  const resp = await fetch(`${API_BASE}/api/mpesa/stk-push`,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      phone, amount, account_ref: accountRef, description
    })
  });
  if(!resp.ok){
    const err = await resp.json();
    throw new Error(err.detail||'Payment initiation failed');
  }
  return resp.json();
}

async function pollPaymentStatus(checkoutRequestId, maxAttempts=20, intervalMs=3000){
  return new Promise((resolve,reject)=>{
    let attempts=0;
    const timer = setInterval(async ()=>{
      attempts++;
      try{
        const resp = await fetch(`${API_BASE}/api/mpesa/status/${checkoutRequestId}`);
        const data = await resp.json();
        if(data.status==='paid'){
          clearInterval(timer);
          resolve(data);
        } else if(data.status==='failed'||data.status==='cancelled'||data.status==='timeout'){
          clearInterval(timer);
          reject(new Error(data.reason||'Payment '+data.status));
        } else if(attempts>=maxAttempts){
          clearInterval(timer);
          reject(new Error('Payment timed out. Please try again.'));
        }
      }catch(e){
        if(attempts>=maxAttempts){
          clearInterval(timer);
          reject(e);
        }
      }
    }, intervalMs);
  });
}

async function createBooking(data){
  const resp = await fetch(`${API_BASE}/api/bookings`,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(data)
  });
  if(!resp.ok) throw new Error('Failed to create booking');
  return resp.json();
}

// ─── NAVBAR HTML ───────────────────────────────────────────────
function navHTML(active=''){
  const user = (() => { try { return JSON.parse(localStorage.getItem('ss_user')); } catch(e) { return null; } })();
  const token = localStorage.getItem('ss_token');
  const isLoggedIn = !!(user && token);

  const authBtns = isLoggedIn
    ? `<span style="font-size:.82rem;color:var(--muted);padding:0 8px">Hi, ${user.name?.split(' ')[0] || 'Guest'}</span>
       ${user.role === 'admin' ? `<a href="admin.html" class="btn btn-ghost btn-sm">Admin</a>` : ''}
       <button class="btn btn-ghost btn-sm" onclick="doLogout()">Logout</button>`
    : `<a href="login.html" class="btn btn-ghost btn-sm">Login</a>
       <a href="register.html" class="btn btn-primary btn-sm">Register</a>`;

  const mobAuthBtns = isLoggedIn
    ? `${user.role === 'admin' ? `<a href="admin.html" class="btn btn-ghost btn-sm">Admin</a>` : ''}
       <button class="btn btn-ghost btn-sm" onclick="doLogout()">Logout</button>`
    : `<a href="login.html" class="btn btn-ghost btn-sm">Login</a>
       <a href="register.html" class="btn btn-primary btn-sm">Register</a>`;

  return `
<nav class="navbar" id="navbar">
  <a href="index.html" class="nav-logo">Serenity <span>Spot</span></a>
  <ul class="nav-center">
    <li><a href="index.html" class="${active==='home'?'active':''}">Home</a></li>
    <li><a href="rooms.html" class="${active==='rooms'?'active':''}">Rooms</a></li>
    <li><a href="contact.html" class="${active==='contact'?'active':''}">Contact</a></li>
  </ul>
  <div class="nav-right">${authBtns}</div>
  <button class="ham" id="ham" onclick="toggleDraw()" aria-label="Menu">
    <span></span><span></span><span></span>
  </button>
</nav>
<div class="mobile-drawer" id="mDraw">
  <a href="index.html">Home</a>
  <a href="rooms.html">Rooms</a>
  <a href="contact.html">Contact</a>
  <div class="mob-auth">${mobAuthBtns}</div>
</div>`;
}

function doLogout(){
  localStorage.removeItem('ss_token');
  localStorage.removeItem('ss_user');
  window.location = 'index.html';
}

// ─── FOOTER HTML ───────────────────────────────────────────────
function footerHTML(){
  return `
<footer>
  <div class="footer-grid">
    <div class="footer-brand">
      <span class="nav-logo">Serenity <span>Spot</span></span>
      <p style="margin-top:12px">Premium BnB accommodation in Kisii, Kenya. Book direct for the best rates and a personalized stay.</p>
      <div class="footer-social">
        <a href="#" class="soc-link">${ICONS.facebook}</a>
        <a href="#" class="soc-link">${ICONS.twitter}</a>
        <a href="https://wa.me/254743788467" class="soc-link">${ICONS.whatsapp}</a>
        <a href="mailto:serenityspotbookings@gmail.com" class="soc-link">${ICONS.mail}</a>
      </div>
    </div>
    <div class="f-col">
      <h4>Navigate</h4>
      <ul>
        <li><a href="index.html">Home</a></li>
        <li><a href="rooms.html">Rooms</a></li>
        <li><a href="contact.html">Contact</a></li>
        <li><a href="login.html">Login</a></li>
      </ul>
    </div>
    <div class="f-col">
      <h4>Room Types</h4>
      <ul>
        <li><a href="rooms.html">Studio</a></li>
        <li><a href="rooms.html">1 Bedroom</a></li>
        <li><a href="rooms.html">2 Bedroom</a></li>
        <li><a href="rooms.html">3 Bedroom</a></li>
      </ul>
    </div>
    <div class="f-col">
      <h4>Contact</h4>
      <ul>
        <li><a href="mailto:serenityspotbookings@gmail.com">serenityspotbookings@gmail.com</a></li>
        <li><a href="tel:+254743788467">+254 743 788 467</a></li>
        <li><a href="https://wa.me/254743788467">WhatsApp Us</a></li>
        <li><a href="#">Kisii Town, Kenya</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© 2026 Serenity Spot. All rights reserved.</span>
    <span>Built with &hearts; for Kenya</span>
  </div>
</footer>`;
}

// ─── SHARED INIT ───────────────────────────────────────────────
function sharedInit(){
  window.addEventListener('scroll',()=>{
    const nav=document.getElementById('navbar');
    if(nav) nav.classList.toggle('scrolled', window.scrollY>20);
  });
}
function toggleDraw(){
  document.getElementById('ham').classList.toggle('open');
  document.getElementById('mDraw').classList.toggle('open');
}