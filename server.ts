import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import fs from "fs/promises";

async function startServer() {
  const app = express();
  const PORT = 3000;
  const DATA_PATH = path.join(process.cwd(), "data", "products.json");

  app.use(express.json());

  // GET products from local JSON
  app.get("/api/urunler", async (req, res) => {
    try {
      const data = await fs.readFile(DATA_PATH, "utf-8");
      res.json(JSON.parse(data));
    } catch (error) {
      console.error("Error reading products:", error);
      res.status(500).json({ error: "Failed to read products" });
    }
  });

  // UPDATE product in local JSON
  app.put("/api/urunler/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const updatedProduct = req.body;
      
      const data = await fs.readFile(DATA_PATH, "utf-8");
      let products = JSON.parse(data);
      
      products = products.map((p: any) => p._id === id ? { ...p, ...updatedProduct } : p);
      
      await fs.writeFile(DATA_PATH, JSON.stringify(products, null, 2));
      res.json({ message: "Product updated successfully" });
    } catch (error) {
      console.error("Error updating product:", error);
      res.status(500).json({ error: "Failed to update product" });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
