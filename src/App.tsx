import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Menu as MenuIcon, 
  Search, 
  ShoppingBasket, 
  Languages, 
  Share2, 
  PhoneCall, 
  Plus, 
  Minus,
  X,
  ChevronRight,
  Loader2,
  Settings,
  Trash2,
  Edit2,
  Check,
  ArrowLeft
} from 'lucide-react';

// Firebase
import { initializeApp } from 'firebase/app';
import { 
  getFirestore, 
  collection, 
  onSnapshot, 
  doc, 
  setDoc, 
  updateDoc, 
  getDocs,
  serverTimestamp,
  query,
  limit
} from 'firebase/firestore';
import firebaseConfig from '../firebase-applet-config.json';

const app = initializeApp(firebaseConfig);
const db = getFirestore(app, firebaseConfig.firestoreDatabaseId);

// --- Types ---

interface MenuItem {
  id: string;
  name: string;
  price: number;
  description: string;
  category: string;
  image: string;
  variants?: { name: string; image: string }[];
}

interface CartItem extends MenuItem {
  quantity: number;
}

// --- Components ---

function TopAppBar({ 
  onMenuClick
}: { 
  onMenuClick: () => void; 
}) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-white/90 backdrop-blur-md border-b border-zinc-100 flex items-center justify-center px-5 shadow-sm">
      <button 
        onClick={onMenuClick}
        className="absolute left-5 p-2 hover:bg-brand-primary/5 rounded-full transition-colors text-zinc-500"
      >
        <MenuIcon size={24} />
      </button>
      <span className="font-display font-black text-xl tracking-tight text-brand-primary">
        Eşref Usta Dondurma
      </span>
    </header>
  );
}

function ProductCard({ 
  item, 
  onAdd 
}: { 
  item: MenuItem; 
  onAdd: (item: MenuItem) => void;
  key?: any;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="bg-white rounded-xl overflow-hidden shadow-[0_4px_20px_rgba(137,76,92,0.05)] border border-brand-surface-container-high group"
    >
      <div className="relative aspect-[16/9] w-full overflow-hidden bg-brand-surface-container">
        <img 
          src={item.image} 
          alt={item.name} 
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          loading="lazy"
          referrerPolicy="no-referrer"
        />
        <div className="absolute top-3 right-3 bg-brand-primary text-white px-3 py-1 rounded-lg font-bold text-sm shadow-md">
          {item.price} TL
        </div>
      </div>
      <div className="p-5">
        <h3 className="font-display font-bold text-xl text-brand-on-surface mb-2">
          {item.name}
        </h3>
        
        {item.description && (
          <p className="font-sans text-brand-on-surface-variant text-sm leading-relaxed mb-4 line-clamp-2">
            {item.description}
          </p>
        )}

        <div className="flex gap-3 mt-4">
          <button 
            onClick={() => onAdd(item)}
            className="flex-1 bg-brand-primary text-white font-bold py-3 rounded-xl flex items-center justify-center space-x-2 active:scale-95 transition-all shadow-md hover:shadow-lg"
          >
            <Plus size={18} />
            <span>Ekle</span>
          </button>
          
          {item.variants && item.variants.length > 0 && (
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="px-4 py-3 rounded-xl border border-brand-outline/20 text-brand-primary font-bold text-xs flex items-center gap-1 hover:bg-brand-surface-container transition-colors"
            >
              <span>{isExpanded ? 'Kapat' : 'Çeşitler'}</span>
              <motion.div animate={{ rotate: isExpanded ? 180 : 0 }}>
                <ChevronRight size={14} />
              </motion.div>
            </button>
          )}
        </div>

        <AnimatePresence>
          {isExpanded && item.variants && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-6 mt-6 border-t border-brand-surface-container space-y-3">
                <p className="text-[10px] font-bold uppercase tracking-widest text-brand-outline mb-2">Lezzet Seçenekleri</p>
                <div className="grid grid-cols-2 gap-3">
                  {item.variants.map((v, i) => (
                    <motion.div 
                      key={i}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => onAdd({...item, name: `${item.name} (${v.name})`})}
                      className="flex flex-col bg-brand-surface-container-high/40 p-2 rounded-lg cursor-pointer hover:bg-brand-primary-container/20 transition-colors border border-transparent hover:border-brand-primary/20"
                    >
                      {v.image ? (
                        <img src={v.image} alt={v.name} className="w-full aspect-square object-cover rounded-md mb-2" referrerPolicy="no-referrer" />
                      ) : (
                        <div className="w-full aspect-square bg-brand-primary/10 rounded-md mb-2 flex items-center justify-center text-brand-primary/40">
                          <Plus size={16} />
                        </div>
                      )}
                      <span className="text-[11px] font-bold text-center truncate">{v.name}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

function BottomNavBar({ 
  activeTab, 
  setActiveTab, 
  cartCount 
}: { 
  activeTab: string; 
  setActiveTab: (tab: string) => void;
  cartCount: number;
}) {
  const tabs = [
    { id: 'menu', label: 'Menü', icon: MenuIcon },
    { id: 'search', label: 'Ara', icon: Search },
    { id: 'cart', label: 'Sepetim', icon: ShoppingBasket, count: cartCount },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-zinc-100 rounded-t-[32px] shadow-[0_-4px_30px_rgba(137,76,92,0.1)] flex justify-around items-center px-4 pt-3 pb-8">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button 
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              relative flex flex-col items-center justify-center space-y-1 px-6 py-2 transition-all duration-300
              ${isActive ? 'text-brand-primary' : 'text-zinc-400'}
            `}
          >
            {isActive && (
              <motion.div 
                layoutId="navItem"
                className="absolute inset-0 bg-brand-primary/10 rounded-2xl -z-10"
              />
            )}
            <Icon size={isActive ? 22 : 20} strokeWidth={isActive ? 2.5 : 2} />
            <span className="text-[10px] uppercase font-bold tracking-wider">{tab.label}</span>
            {tab.count !== undefined && tab.count > 0 && (
              <span className="absolute top-1 right-4 bg-brand-primary text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold animate-in zoom-in">
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}

function Sidebar({ isOpen, onClose, onAction }: { isOpen: boolean; onClose: () => void; onAction: (id: string) => void }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]"
          />
          <motion.div 
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 left-0 bottom-0 w-[280px] bg-brand-background z-[101] shadow-2xl p-6"
          >
            <div className="flex justify-between items-center mb-10">
              <span className="font-display font-black text-xl text-brand-primary">Menü</span>
              <button onClick={onClose} className="p-2 bg-brand-surface-container rounded-full text-zinc-500">
                <X size={20} />
              </button>
            </div>
            
            <div className="space-y-4">
              {['Hakkımızda', 'Şubelerimiz', 'Kampanyalar', 'İletişim'].map((item) => (
                <button 
                  key={item}
                  onClick={() => { onAction(item); onClose(); }}
                  className="w-full text-left font-bold text-brand-on-surface py-3 border-b border-brand-surface-container flex justify-between items-center group"
                >
                  {item}
                  <ChevronRight size={16} className="text-brand-outline group-hover:text-brand-primary transition-colors" />
                </button>
              ))}
            </div>

            <div className="absolute bottom-10 left-6 right-6">
              <div className="bg-brand-primary-container/30 p-4 rounded-2xl text-center">
                <p className="text-[10px] font-bold text-brand-on-primary-container uppercase tracking-widest mb-1">Müşteri Destek</p>
                <p className="text-lg font-black text-brand-primary">444 0 555</p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function AdminPanel({ 
  items, 
  onUpdateItem,
  onBack,
  categories
}: { 
  items: MenuItem[]; 
  onUpdateItem: (updatedItem: MenuItem) => void;
  onBack: () => void;
  categories: string[];
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<MenuItem>>({});
  const [password, setPassword] = useState("");
  const [isAuthorized, setIsAuthorized] = useState(false);

  const handleLogin = () => {
    if (password === "admin123") {
      setIsAuthorized(true);
    } else {
      alert("Hatalı şifre!");
    }
  };

  if (!isAuthorized) {
    return (
      <div className="py-20 flex flex-col items-center justify-center space-y-6">
        <div className="bg-brand-primary/10 p-6 rounded-full text-brand-primary">
          <Settings size={48} />
        </div>
        <div className="text-center">
          <h2 className="font-display font-black text-2xl mb-2">Panel Girişi</h2>
          <p className="text-sm text-brand-on-surface-variant">Lütfen yönetim şifresini girin.</p>
        </div>
        <div className="w-full max-w-xs space-y-4">
          <input 
            type="password"
            placeholder="Şifre"
            className="w-full bg-white border border-brand-surface-container-high p-4 rounded-2xl outline-none focus:ring-2 focus:ring-brand-primary/20 text-center font-bold"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
          />
          <button 
            onClick={handleLogin}
            className="w-full bg-brand-primary text-white py-4 rounded-2xl font-black shadow-lg shadow-brand-primary/20 active:scale-95 transition-transform"
          >
            Giriş Yap
          </button>
          <button onClick={onBack} className="w-full text-brand-outline font-bold text-sm">Geri Dön</button>
        </div>
      </div>
    );
  }

  const handleEdit = (item: MenuItem) => {
    setEditingId(item.id);
    setFormData(item);
  };

  const handleAddNew = () => {
    const newId = `new-${Date.now()}`;
    setEditingId(newId);
    setFormData({
      id: newId,
      name: "",
      price: 0,
      category: categories[1] || "Diğer",
      image: ""
    });
  };

  const handleSave = () => {
    if (editingId) {
      onUpdateItem({ ...formData } as MenuItem);
      setEditingId(null);
      setFormData({});
    }
  };

  return (
    <div className="animate-in fade-in duration-500">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 bg-brand-surface-container rounded-full text-brand-primary">
            <ArrowLeft size={20} />
          </button>
          <h2 className="font-display font-black text-2xl text-brand-on-surface">Yönetim</h2>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleAddNew}
            className="bg-brand-primary text-white px-4 py-2 rounded-xl font-bold text-xs shadow-lg shadow-brand-primary/20 active:scale-95 transition-transform"
          >
            Yeni Ekle
          </button>
          <button onClick={() => setIsAuthorized(false)} className="text-xs font-bold text-red-500 p-2">Çıkış</button>
        </div>
      </div>

      <div className="space-y-4">
        {editingId && editingId.startsWith('new-') && (
          <div className="bg-brand-primary/5 p-6 rounded-3xl border-2 border-dashed border-brand-primary/30 mb-8 animate-in slide-in-from-top duration-300">
            <h3 className="font-black mb-4 text-brand-primary flex items-center gap-2">
              <Plus size={20} /> Yeni Ürün Ekle
            </h3>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-bold uppercase text-brand-outline">Ürün Adı</label>
                <input 
                  className="w-full bg-white p-3 rounded-xl mt-1 font-bold outline-none border border-brand-surface-container-high"
                  placeholder="Örn: Karışık Dondurma"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold uppercase text-brand-outline">Fiyat (TL)</label>
                  <input 
                    type="number"
                    className="w-full bg-white p-3 rounded-xl mt-1 font-bold outline-none border border-brand-surface-container-high"
                    value={formData.price || 0}
                    onChange={(e) => setFormData({...formData, price: Number(e.target.value)})}
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-brand-outline">Kategori</label>
                  <select 
                    className="w-full bg-white p-3 rounded-xl mt-1 font-bold outline-none border border-brand-surface-container-high"
                    value={formData.category || ''}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                  >
                    {categories.filter(c => c !== 'Tümü').map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase text-brand-outline">Görsel URL</label>
                <input 
                  className="w-full bg-white p-3 rounded-xl mt-1 text-xs outline-none border border-brand-surface-container-high"
                  placeholder="https://gorsel-linki.com/resim.jpg"
                  value={formData.image || ''}
                  onChange={(e) => setFormData({...formData, image: e.target.value})}
                />
              </div>
              <div className="flex gap-3">
                <button 
                  onClick={handleSave} 
                  className="flex-1 bg-brand-primary text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-brand-primary/20"
                >
                  <Check size={18} /> Kaydet
                </button>
                <button 
                  onClick={() => {setEditingId(null); setFormData({});}}
                  className="px-6 py-3 bg-brand-surface-container text-brand-outline rounded-xl font-bold"
                >
                  İptal
                </button>
              </div>
            </div>
          </div>
        )}

        {items.map((item) => (
          <div key={item.id} className="bg-white p-4 rounded-2xl shadow-sm border border-brand-surface-container overflow-hidden">
            {editingId === item.id ? (
              <div className="space-y-4">
                <div>
                  <label className="text-[10px] font-bold uppercase text-brand-outline">Ürün Düzenle</label>
                  <input 
                    className="w-full bg-brand-surface-container p-3 rounded-xl mt-1 font-bold outline-none ring-brand-primary-container focus:ring-2"
                    value={formData.name || ''}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-bold uppercase text-brand-outline">Fiyat (TL)</label>
                    <input 
                      type="number"
                      className="w-full bg-brand-surface-container p-3 rounded-xl mt-1 font-bold outline-none"
                      value={formData.price || 0}
                      onChange={(e) => setFormData({...formData, price: Number(e.target.value)})}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-brand-outline">Kategori</label>
                    <input 
                      className="w-full bg-brand-surface-container p-3 rounded-xl mt-1 font-bold outline-none"
                      value={formData.category || ''}
                      onChange={(e) => setFormData({...formData, category: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-brand-outline">Görsel URL</label>
                  <input 
                    className="w-full bg-brand-surface-container p-3 rounded-xl mt-1 text-xs outline-none"
                    value={formData.image || ''}
                    onChange={(e) => setFormData({...formData, image: e.target.value})}
                  />
                </div>
                <div className="flex gap-3">
                  <button onClick={handleSave} className="flex-1 bg-brand-primary text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2">
                    <Check size={18} /> Güncelle
                  </button>
                  <button onClick={() => {setEditingId(null); setFormData({});}} className="px-6 py-3 bg-brand-surface-container text-brand-outline rounded-xl font-bold">
                    İptal
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded-xl shadow-sm" referrerPolicy="no-referrer" />
                <div className="flex-1">
                  <h4 className="font-bold text-brand-on-surface">{item.name}</h4>
                  <p className="text-sm font-bold text-brand-primary">{item.price} TL • {item.category}</p>
                </div>
                <button onClick={() => handleEdit(item)} className="p-3 bg-brand-surface-container rounded-xl text-brand-secondary">
                  <Edit2 size={18} />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CartView({ 
  items, 
  onUpdateQuantity, 
  onRemove,
  onBack 
}: { 
  items: CartItem[]; 
  onUpdateQuantity: (id: string, delta: number) => void;
  onRemove: (id: string) => void;
  onBack: () => void;
}) {
  const total = items.reduce((acc, curr) => acc + (curr.price * curr.quantity), 0);

  return (
    <div className="animate-in fade-in duration-500 pb-20">
      <div className="flex items-center gap-3 mb-8">
        <button onClick={onBack} className="p-2 bg-brand-surface-container rounded-full text-brand-primary">
          <ArrowLeft size={20} />
        </button>
        <h2 className="font-display font-black text-2xl text-brand-on-surface">Sepetim</h2>
      </div>

      {items.length === 0 ? (
        <div className="py-20 text-center space-y-4">
          <div className="inline-flex items-center justify-center p-8 bg-brand-surface-container rounded-full text-brand-outline">
            <ShoppingBasket size={48} />
          </div>
          <p className="font-bold text-brand-on-surface-variant">Sepetiniz şu an boş.</p>
          <button onClick={onBack} className="bg-brand-primary text-white px-8 py-3 rounded-xl font-bold">Alışverişe Başla</button>
        </div>
      ) : (
        <>
          <div className="space-y-4 mb-8">
            {items.map((item) => (
              <div key={item.id} className="bg-white p-4 rounded-2xl shadow-sm border border-brand-surface-container flex items-center gap-4">
                <img src={item.image} alt={item.name} className="w-16 h-16 object-cover rounded-xl" referrerPolicy="no-referrer" />
                <div className="flex-1">
                  <h4 className="font-bold text-brand-on-surface text-sm">{item.name}</h4>
                  <p className="text-xs font-bold text-brand-primary">{item.price} TL</p>
                </div>
                <div className="flex items-center bg-brand-surface-container rounded-xl p-1">
                  <button onClick={() => onUpdateQuantity(item.id, -1)} className="p-1 text-zinc-500">
                    <Minus size={14} />
                  </button>
                  <span className="w-8 text-center font-bold text-sm">{item.quantity}</span>
                  <button onClick={() => onUpdateQuantity(item.id, 1)} className="p-1 text-zinc-500">
                    <Plus size={14} />
                  </button>
                </div>
                <button onClick={() => onRemove(item.id)} className="p-2 text-red-400">
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>

          <div className="bg-brand-primary text-white p-6 rounded-3xl shadow-xl shadow-brand-primary/20">
            <div className="flex justify-between items-center mb-4">
              <span className="font-bold opacity-80 uppercase text-xs tracking-widest">Genel Toplam</span>
              <span className="text-2xl font-black">{total} TL</span>
            </div>
            <button className="w-full bg-white text-brand-primary py-4 rounded-2xl font-black text-lg shadow-sm active:scale-95 transition-transform">
              Siparişi Tamamla
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState("Tümü");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("menu");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const productsRef = collection(db, 'products');
    
    // Seed initial data if empty
    const seedData = async () => {
      const q = query(productsRef, limit(1));
      const snap = await getDocs(q);
      if (snap.empty) {
        console.log("Seeding initial products...");
        const initialProducts = [
          { ad: "Dondurma (Top)", fiyat: 20, img: "https://i.ibb.co/qMm8HG95/25acf666340c.jpg", kategori: "Dondurma" },
          { ad: "Hamsiköy Sütlaç", fiyat: 100, img: "https://i.ibb.co/8L6dGCPW/442f0f98bdce.jpg", kategori: "Tatlılar" },
          { ad: "Meyveli Soda", fiyat: 25, img: "https://i.ibb.co/xKJ4HkzG/813c2bafa07d.jpg", kategori: "İçecekler" },
          { ad: "Sade Soda", fiyat: 20, img: "https://i.ibb.co/KpRv0FkS/920ceaa473da.jpg", kategori: "İçecekler" },
          { ad: "Su", fiyat: 15, img: "https://i.ibb.co/G4tBVRmP/6c661f12a995.jpg", kategori: "İçecekler" },
          { ad: "Çiğköfte Dürüm", fiyat: 80, img: "https://i.ibb.co/TDSpxVMX/97886b15e606.jpg", kategori: "Çiğköfte" },
          { ad: "Türk Kahvesi", fiyat: 45, img: "https://i.ibb.co/6cVcSKwr/8725bad50158.jpg", kategori: "İçecekler" },
          { ad: "Oralet Çeşitleri", fiyat: 15, img: "https://i.ibb.co/RksTLmzy/3a1c150e9e67.jpg", kategori: "İçecekler" },
          { ad: "Çay", fiyat: 15, img: "https://i.ibb.co/MHXkbc3/6446b8d1e8dd.jpg", kategori: "İçecekler" }
        ];
        for (const p of initialProducts) {
          await setDoc(doc(productsRef), { ...p, updatedAt: serverTimestamp() });
        }
      }
    };
    seedData();

    setLoading(true);
    const unsubscribe = onSnapshot(productsRef, (snapshot) => {
      const fetchedItems: MenuItem[] = snapshot.docs.map(docSnap => {
        const data = docSnap.data();
        let item: MenuItem = {
          id: docSnap.id,
          name: data.ad,
          price: data.fiyat,
          image: data.img,
          category: data.kategori,
          description: ""
        };

        const lowerName = item.name.toLowerCase();
        if (lowerName.includes("dondurma (top)")) {
          item.description = "Eşref Usta'nın meşhur dondurmaları. İstediğiniz aromayı seçin.";
          item.variants = [
            { name: "Sade", image: "" }, { name: "Kakao", image: "" }, { name: "Limon", image: "" },
            { name: "Çilek", image: "" }, { name: "Karamel", image: "" }, { name: "Kavun", image: "" },
            { name: "Aronia", image: "" }, { name: "Şeftali", image: "" }, { name: "Böğürtlen", image: "" },
            { name: "İncir", image: "" }, { name: "Ceviz", image: "" }, { name: "Yoğurtlu Meyveli", image: "" },
            { name: "Antep Fıstığı", image: "" }, { name: "Vişne", image: "" }, { name: "Oreo", image: "" },
            { name: "Karpuz", image: "" }, { name: "Ballı Muz", image: "" }, { name: "Ballı Badem", image: "" },
            { name: "Damla Sakızı", image: "" }, { name: "Yeşil Elma", image: "" }, { name: "Karadut", image: "" },
            { name: "Big Bubble", image: "" }, { name: "Kivi", image: "" }, { name: "Mango", image: "" },
            { name: "Orman Meyveli", image: "" }
          ];
        }

        if (lowerName.includes("meyveli soda") || lowerName.includes("sade soda")) {
          item.description = "Ferahlatıcı meyve seçenekleriyle özel soda keyfi.";
          item.variants = [
            { name: "Çilek & Karpuz", image: "" },
            { name: "Nar", image: "" },
            { name: "Sade", image: "" },
            { name: "Limon", image: "" },
            { name: "Guava", image: "" }
          ];
        }
        return item;
      });

      setItems(fetchedItems);
      setCategories(["Tümü", ...Array.from(new Set(fetchedItems.map(i => i.category)))]);
      setLoading(false);
    }, (err) => {
      setError(err.message);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const filteredItems = useMemo(() => {
    return items.filter(item => 
      (activeCategory === "Tümü" || item.category === activeCategory) && 
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [items, activeCategory, searchQuery]);

  const handleAddToCart = (item: MenuItem) => {
    setCart(prev => {
      const existing = prev.find(p => p.id === item.id && p.name === item.name);
      if (existing) {
        return prev.map(p => p.id === item.id && p.name === item.name ? {...p, quantity: p.quantity + 1} : p);
      }
      return [...prev, {...item, quantity: 1}];
    });
  };

  const handleUpdateQuantity = (id: string, delta: number) => {
    setCart(prev => prev.map(p => 
      p.id === id ? {...p, quantity: Math.max(1, p.quantity + delta)} : p
    ));
  };

  const handleRemoveFromCart = (id: string) => {
    setCart(prev => prev.filter(p => p.id !== id));
  };

  const handleUpdateItem = async (updated: MenuItem) => {
    try {
      if (updated.id.startsWith('new-')) {
        // Create new item
        const productsRef = collection(db, 'products');
        await setDoc(doc(productsRef), {
          ad: updated.name,
          fiyat: updated.price,
          img: updated.image,
          kategori: updated.category,
          updatedAt: serverTimestamp()
        });
      } else {
        // Update existing item
        const productRef = doc(db, 'products', updated.id);
        await updateDoc(productRef, {
          ad: updated.name,
          fiyat: updated.price,
          img: updated.image,
          kategori: updated.category,
          updatedAt: serverTimestamp()
        });
      }
    } catch (err) {
      console.error('Error updating item:', err);
      alert('İşlem başarısız!');
    }
  };

  return (
    <div className="min-h-screen bg-brand-background pb-32">
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)} 
        onAction={(id) => console.log(id)} 
      />
      
      <TopAppBar 
        onMenuClick={() => setIsSidebarOpen(true)} 
      />

      <main className="pt-24 px-5 max-w-2xl mx-auto">
        <AnimatePresence mode="wait">
          {activeTab === 'menu' && (
            <motion.div key="menu" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
              {/* Hero */}
              <header className="mb-8">
                <h1 className="font-display text-4xl font-black text-brand-primary mb-3">Taptaze Lezzetler</h1>
                <p className="text-brand-on-surface-variant font-medium">Babadan oğula devredilen dondurma sanatı.</p>
              </header>

              {/* Categories */}
              <nav className="flex space-x-3 mb-8 overflow-x-auto pb-4 scrollbar-hide">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setActiveCategory(cat)}
                    className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all ${activeCategory === cat ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20 bg-gradient-to-br from-brand-primary to-brand-tertiary' : 'bg-white text-brand-on-surface-variant shadow-sm'}`}
                  >
                    {cat}
                  </button>
                ))}
              </nav>

              {/* Grid */}
              <div className="space-y-6">
                {loading ? (
                  <div className="py-20 flex flex-col items-center justify-center text-brand-outline">
                    <Loader2 className="animate-spin mb-4" size={40} />
                    <p className="font-bold text-sm uppercase tracking-widest">Yükleniyor...</p>
                  </div>
                ) : (
                  <div className="grid gap-6">
                    {filteredItems.map((item: MenuItem) => (
                      <ProductCard key={item.id} item={item} onAdd={handleAddToCart} />
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'search' && (
            <motion.div key="search" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
              <div className="mb-8 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-outline" size={20} />
                <input 
                  autoFocus
                  placeholder="Ürün ismiyle ara..."
                  className="w-full bg-white border-none rounded-2xl py-4 pl-12 pr-6 shadow-sm focus:ring-2 focus:ring-brand-primary-container outline-none"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="grid gap-6">
                {filteredItems.map((item: MenuItem) => (
                  <ProductCard key={item.id} item={item} onAdd={handleAddToCart} />
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'cart' && (
            <motion.div key="cart" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
              <CartView 
                items={cart} 
                onUpdateQuantity={handleUpdateQuantity} 
                onRemove={handleRemoveFromCart}
                onBack={() => setActiveTab('menu')}
              />
            </motion.div>
          )}

          {activeTab === 'admin' && (
            <motion.div key="admin" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
              <AdminPanel 
                items={items} 
                onUpdateItem={handleUpdateItem}
                onBack={() => setActiveTab('menu')}
                categories={categories}
              />
            </motion.div>
          )}
        </AnimatePresence>
        
        <footer className="mt-20 pt-12 border-t border-brand-surface-container text-center pb-8">
          <div className="text-[10px] text-brand-outline font-bold uppercase tracking-[0.2em] mb-4">
            © 2026 Eşref Usta Dondurma
          </div>
          <button 
            onClick={() => setActiveTab('admin')}
            className="text-[10px] text-brand-outline/40 hover:text-brand-primary font-bold uppercase tracking-widest transition-colors"
          >
            Yönetim Paneli
          </button>
        </footer>
      </main>

      <BottomNavBar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        cartCount={cart.reduce((a, b) => a + b.quantity, 0)} 
      />
    </div>
  );
}
