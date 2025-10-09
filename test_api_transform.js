// Quick test of the transformation logic
const { readFileSync } = require("fs");
const { join } = require("path");

// Load scraped data
function loadScrapedData() {
  try {
    const filePath = join(
      process.cwd(),
      "macbook_scraper",
      "output",
      "latest_products.json",
    );
    const jsonData = readFileSync(filePath, "utf-8");
    const data = JSON.parse(jsonData);
    return data.products || [];
  } catch (error) {
    console.error("Error loading scraped data:", error.message);
    return [];
  }
}

// Transform function (same as API)
function transformScrapedProduct(product) {
  const modelName = product.model || "";
  const modelLower = modelName.toLowerCase();

  let modelType = "MacBook";
  let screenSize = "";
  if (modelLower.includes("air")) {
    modelType = "MacBook Air";
    if (modelLower.includes("13")) screenSize = '13"';
    else if (modelLower.includes("15")) screenSize = '15"';
  } else if (modelLower.includes("pro")) {
    modelType = "MacBook Pro";
    if (modelLower.includes("14")) screenSize = '14"';
    else if (modelLower.includes("16")) screenSize = '16"';
  }

  let category = "Unknown";
  if (modelLower.includes("m4 max")) category = "M4 Max";
  else if (modelLower.includes("m4 pro")) category = "M4 Pro";
  else if (modelLower.includes("m4")) category = "M4";
  else if (modelLower.includes("m3 max")) category = "M3 Max";
  else if (modelLower.includes("m3 pro")) category = "M3 Pro";
  else if (modelLower.includes("m3")) category = "M3";
  else if (modelLower.includes("m2")) category = "M2";
  else if (modelLower.includes("m1")) category = "M1";

  return {
    model: screenSize ? `${modelType} ${screenSize}` : modelType,
    modelType: modelType,
    screenSize: screenSize,
    category: category,
    configuration: modelName,
    scraped: true,
    shop: product.shop,
  };
}

// Test it
const scrapedProducts = loadScrapedData();
console.log(`\n📊 Total scraped products: ${scrapedProducts.length}\n`);

const cellphonesProducts = scrapedProducts
  .filter((p) => p.shop === "cellphones")
  .map(transformScrapedProduct);

console.log(`✅ CellphoneS products after transform: ${cellphonesProducts.length}\n`);

if (cellphonesProducts.length > 0) {
  console.log("📋 First 3 products:\n");
  cellphonesProducts.slice(0, 3).forEach((p, i) => {
    console.log(`${i + 1}. ${p.model}`);
    console.log(`   Config: ${p.configuration}`);
    console.log(`   Category: ${p.category}`);
    console.log(`   Shop: ${p.shop}`);
    console.log(`   Scraped: ${p.scraped}\n`);
  });
} else {
  console.log("❌ No products after transformation!");
}

// Check for empty configurations
const emptyConfigs = cellphonesProducts.filter(p => !p.configuration || p.configuration === "");
console.log(`\n⚠️  Products with empty config: ${emptyConfigs.length}`);

if (emptyConfigs.length > 0) {
  console.log("Empty products:");
  emptyConfigs.forEach(p => {
    console.log(`  - ${p.model} | ${p.category}`);
  });
}
