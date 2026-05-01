import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Menu, 
  Search, 
  ShoppingBasket, 
  Languages, 
  Share2, 
  PhoneCall, 
  Plus, 
  X,
  ChevronRight,
  Loader2
} from 'lucide-react';

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

interface ApiItem {
  _id: string;
  ad: string;
  fiyat: number;
  img: string;
  kategori: string;
}

// --- Components ---

function TopAppBar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-white/90 backdrop-blur-md border-b border-zinc-100 flex items-center justify-between px-5 shadow-sm">
      <button className="p-2 hover:bg-brand-primary/5 rounded-full transition-colors text-zinc-500">
        <Menu size={24} />
      </button>
      <span className="font-display font-black text-xl tracking-tight text-brand-primary">
        Eşref Usta Dondurma
      </span>
      <button className="p-2 hover:bg-brand-primary/5 rounded-full transition-colors text-zinc-500">
        <Languages size={24} />
      </button>
    </header>
  );
}

function ProductCard({ item, onAdd }: { item: MenuItem; onAdd: () => void }) {
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
        <div className="absolute top-3 right-3 bg-brand-primary-container text-brand-on-primary-container px-3 py-1 rounded-lg font-semibold text-sm shadow-sm">
          {item.price} TL
        </div>
      </div>
      <div className="p-5">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-display font-bold text-xl text-brand-on-surface">
            {item.name}
          </h3>
        </div>
        
        {item.description && (
          <p className="font-sans text-brand-on-surface-variant text-sm leading-relaxed mb-4 line-clamp-2">
            {item.description}
          </p>
        )}

        <div className="flex gap-3 mt-4">
          <button 
            onClick={onAdd}
            className="flex-1 bg-brand-primary text-white font-semibold py-3 rounded-full flex items-center justify-center space-x-2 active:scale-95 transition-all shadow-md hover:bg-brand-primary/90"
          >
            <Plus size={18} />
            <span>Ekle</span>
          </button>
          
          {item.variants && item.variants.length > 0 && (
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="px-4 py-3 rounded-full border border-brand-outline/20 text-brand-primary font-bold text-sm flex items-center gap-2 hover:bg-brand-surface-container transition-colors"
            >
              <span>{isExpanded ? 'Seç' : 'Çeşitleri Gör'}</span>
              <motion.div animate={{ rotate: isExpanded ? 180 : 0 }}>
                <ChevronRight size={16} />
              </motion.div>
            </button>
          )}
        </div>

        {/* Variants Expansion */}
        <AnimatePresence>
          {isExpanded && item.variants && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="pt-6 mt-6 border-t border-brand-surface-container space-y-3">
                <p className="text-[10px] font-bold uppercase tracking-widest text-brand-outline mb-2">Mevcut Çeşitler</p>
                <div className="grid grid-cols-2 gap-3">
                  {item.variants.map((v, i) => (
                    <motion.div 
                      key={i}
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={onAdd}
                      className="flex flex-col bg-brand-surface-container-high/40 p-2 rounded-lg cursor-pointer hover:bg-brand-primary-container/20 transition-colors border border-transparent hover:border-brand-primary/20"
                    >
                      <img src={v.image} alt={v.name} className="w-full aspect-[4/3] object-cover rounded-md mb-2" referrerPolicy="no-referrer" />
                      <span className="text-xs font-bold text-center truncate">{v.name}</span>
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

function BottomNavBar({ cartCount }: { cartCount: number }) {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-zinc-100 rounded-t-[32px] shadow-[0_-4px_20px_rgba(244,167,185,0.15)] flex justify-around items-center px-4 pt-3 pb-8">
      <button className="flex flex-col items-center justify-center space-y-1 bg-brand-primary-container/30 text-brand-primary rounded-2xl px-6 py-2 transition-all">
        <Menu size={20} />
        <span className="text-[10px] uppercase font-bold tracking-wider">Menü</span>
      </button>
      <button className="flex flex-col items-center justify-center space-y-1 text-zinc-400 px-6 py-2 hover:text-brand-primary transition-all">
        <Search size={20} />
        <span className="text-[10px] uppercase font-bold tracking-wider">Ara</span>
      </button>
      <button className="relative flex flex-col items-center justify-center space-y-1 text-zinc-400 px-6 py-2 hover:text-brand-primary transition-all">
        <ShoppingBasket size={20} />
        <span className="text-[10px] uppercase font-bold tracking-wider">Sepetim</span>
        {cartCount > 0 && (
          <span className="absolute top-1 right-5 bg-brand-primary text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold">
            {cartCount}
          </span>
        )}
      </button>
    </nav>
  );
}

export default function App() {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [cartCount, setCartCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch('https://e-ref-api.onrender.com/api/urunler');
        if (!response.ok) throw new Error('Ürünler yüklenirken bir hata oluştu');
        const data: ApiItem[] = await response.json();
        
        let mappedItems: MenuItem[] = data.map(item => ({
          id: item._id,
          name: item.ad,
          price: item.fiyat,
          image: item.img,
          category: item.kategori,
          description: "" 
        }));

        // Augment data with variants grouping
        mappedItems = mappedItems.map(item => {
          if (item.name.includes("Dondurma (Top)")) {
            return {
              ...item,
              description: "Eşref Usta'nın meşhur dondurmaları. İstediğiniz aromayı seçin.",
              variants: [
                { name: "Sade Maraş", image: "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=800&auto=format&fit=crop&q=60" },
                { name: "Antep Fıstıklı", image: "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=800&auto=format&fit=crop&q=60" },
                { name: "Belçika Çikolatalı", image: "https://images.unsplash.com/photo-1560008511-11c63416e52d?w=800&auto=format&fit=crop&q=60" },
                { name: "Karadutlu", image: "https://images.unsplash.com/photo-1561845730-208ad5910553?w=800&auto=format&fit=crop&q=60" },
                { name: "Limonlu", image: "https://images.unsplash.com/photo-1534706936160-d5ee67733576?w=800&auto=format&fit=crop&q=60" },
                { name: "Bal Bademli", image: "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=800&auto=format&fit=crop&q=60" },
                { name: "Vişneli", image: "https://images.unsplash.com/photo-1534706636972-29737133024c?w=800&auto=format&fit=crop&q=60" },
                { name: "Karamelli", image: "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=800&auto=format&fit=crop&q=60" }
              ]
            };
          }
          if (item.name.includes("Oralet")) {
            return {
              ...item,
              description: "Mayve aromalı sıcak içecek keyfi.",
              variants: [
                { name: "Portakal", image: "https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=800&auto=format&fit=crop&q=60" },
                { name: "Kuşburnu", image: "https://images.unsplash.com/photo-1515233215286-905a5a176274?w=800&auto=format&fit=crop&q=60" },
                { name: "Elma", image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=800&auto=format&fit=crop&q=60" },
                { name: "Limon", image: "https://images.unsplash.com/photo-1534706936160-d5ee67733576?w=800&auto=format&fit=crop&q=60" },
                { name: "Kivi", image: "https://images.unsplash.com/photo-1510005391300-3f74f76ca024?w=800&auto=format&fit=crop&q=60" }
              ]
            };
          }
          return item;
        });

        const uniqueCategories = Array.from(new Set(mappedItems.map(i => i.category)));
        
        setItems(mappedItems);
        setCategories(["Tümü", ...uniqueCategories]);
        setActiveCategory("Tümü");
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Bir hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredItems = items.filter(item => 
    (activeCategory === "Tümü" || item.category === activeCategory) && 
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddToCart = () => {
    setCartCount(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-brand-background pb-32 md:pb-12">
      <TopAppBar />

      <main className="pt-24 px-5 max-w-2xl mx-auto">
        {/* Hero Section */}
        <header className="mb-8">
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="font-display text-4xl leading-[1.1] font-black text-brand-primary mb-3"
          >
            Lezzetli bir dondurma deneyimine hoş geldiniz
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="text-brand-on-surface-variant font-medium"
          >
            Ustalıkla hazırlanan, serinleten tatlar.
          </motion.p>
        </header>

        {/* Search Bar */}
        <section className="mb-8 relative group">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 p-1 text-brand-outline transition-colors group-focus-within:text-brand-primary">
            <Search size={20} />
          </div>
          <input 
            type="text" 
            placeholder="Tat arayın..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-brand-surface-container-high/50 border-none rounded-full py-4 pl-12 pr-6 text-brand-on-surface placeholder:text-brand-outline focus:ring-2 focus:ring-brand-primary-container outline-none transition-all shadow-sm"
          />
        </section>

        {/* Categories */}
        <nav className="flex space-x-3 mb-8 overflow-x-auto pb-4 scrollbar-hide">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`
                px-6 py-2.5 rounded-full whitespace-nowrap font-bold text-sm transition-all shadow-sm
                ${activeCategory === cat 
                  ? 'bg-brand-primary text-white scale-105' 
                  : 'bg-brand-surface-container text-brand-on-surface-variant hover:bg-brand-surface-container-high'}
              `}
            >
              {cat}
            </button>
          ))}
        </nav>

        {/* Content List */}
        <section className="space-y-6">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-4 text-brand-outline">
              <Loader2 className="animate-spin" size={40} />
              <p className="font-bold text-sm uppercase tracking-wider">Menü Yükleniyor...</p>
            </div>
          ) : error ? (
            <div className="py-20 text-center space-y-4">
              <div className="inline-flex items-center justify-center p-6 bg-red-50 rounded-full text-red-500">
                <X size={32} />
              </div>
              <p className="text-red-600 font-medium">{error}</p>
              <button 
                onClick={() => window.location.reload()}
                className="bg-brand-primary text-white px-6 py-2 rounded-full font-bold text-sm"
              >
                Tekrar Dene
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-display font-bold text-lg text-brand-on-surface flex items-center gap-2">
                  <ChevronRight size={18} className="text-brand-primary" />
                  {activeCategory}
                </h2>
                <span className="text-xs font-bold text-brand-outline uppercase tracking-widest">
                  {filteredItems.length} Ürün
                </span>
              </div>

              <AnimatePresence mode="popLayout">
                {filteredItems.length > 0 ? (
                  <div className="grid gap-6">
                    {filteredItems.map((item) => (
                      <div key={item.id}>
                        <ProductCard 
                          item={item} 
                          onAdd={handleAddToCart} 
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="py-20 text-center space-y-4"
                  >
                    <div className="inline-flex items-center justify-center p-6 bg-brand-surface-container rounded-full text-brand-outline">
                      <X size={32} />
                    </div>
                    <p className="text-brand-on-surface-variant font-medium">Aradığınız kriterlere uygun ürün bulunamadı.</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          )}
        </section>

        {/* Footer */}
        <footer className="mt-20 pt-12 border-t border-brand-surface-container text-center pb-8">
          <h4 className="font-display font-bold text-xl text-brand-on-surface mb-3">İletişim</h4>
          <p className="text-brand-on-surface-variant text-sm mb-6 max-w-[240px] mx-auto leading-relaxed">
            info@esrefusta.com<br />
            <span className="font-bold">+90 555 123 4567</span>
          </p>
          <div className="flex justify-center space-x-4">
            <a href="#" className="p-3 bg-brand-surface-container hover:bg-brand-primary-container/20 rounded-full text-brand-tertiary transition-all" referrerPolicy="no-referrer">
              <Share2 size={20} />
            </a>
            <a href="#" className="p-3 bg-brand-surface-container hover:bg-brand-primary-container/20 rounded-full text-brand-tertiary transition-all" referrerPolicy="no-referrer">
              <PhoneCall size={20} />
            </a>
          </div>
          <div className="mt-12 text-[10px] text-brand-outline font-bold uppercase tracking-[0.2em]">
            © 2026 Eşref Usta Dondurma
          </div>
        </footer>
      </main>

      <BottomNavBar cartCount={cartCount} />
    </div>
  );
}
