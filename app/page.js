"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  RefreshCw,
  Smartphone,
  Globe,
  Calculator,
  Store,
  Filter,
  ArrowUpDown,
} from "lucide-react";
import { toast } from "sonner";

export default function MacBookTracker() {
  const [marketplaceData, setMarketplaceData] = useState({
    fptShop: [],
    shopDunk: [],
    topZone: [],
    cellphones: [],
  });
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [exchangeRate, setExchangeRate] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [sortOrder, setSortOrder] = useState("default"); // default, low-to-high, high-to-low

  const fetchPrices = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/macbook-prices");
      const data = await response.json();

      if (data.success) {
        setMarketplaceData(data.marketplaces);
        setExchangeRate(data.exchangeRate);
        setLastUpdate(new Date().toLocaleString());
        toast.success("Prices updated successfully from all marketplaces!");
      } else {
        toast.error(data.error || "Failed to fetch prices");
      }
    } catch (error) {
      console.error("Error fetching prices:", error);
      toast.error("Failed to connect to price service");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrices();
  }, []);

  const formatCurrency = (amount, currency = "INR") => {
    if (currency === "VND") {
      return new Intl.NumberFormat("vi-VN", {
        style: "currency",
        currency: "VND",
      }).format(amount);
    }
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
    }).format(amount);
  };

  const filterAndSortPrices = (prices) => {
    // Filter by category
    let filtered =
      selectedCategory === "All"
        ? prices
        : prices.filter((item) => item.category === selectedCategory);

    // Sort by price
    if (sortOrder === "low-to-high") {
      filtered = [...filtered].sort(
        (a, b) => (a.finalPrice || 0) - (b.finalPrice || 0),
      );
    } else if (sortOrder === "high-to-low") {
      filtered = [...filtered].sort(
        (a, b) => (b.finalPrice || 0) - (a.finalPrice || 0),
      );
    }

    return filtered;
  };

  const categories = ["All", "M4", "M4 Pro", "M4 Max", "M3 Max"];

  const renderPriceTable = (prices, marketplaceName) => {
    const filteredPrices = filterAndSortPrices(prices);

    return (
      <Card className="bg-white/90 backdrop-blur-sm shadow-xl mb-8">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Store className="h-6 w-6 text-indigo-600" />
            <CardTitle className="text-2xl text-gray-900">
              {marketplaceName}
            </CardTitle>
          </div>
          <CardDescription className="text-gray-600">
            All prices converted to INR with 8.5% effective VAT refund for
            tourists
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && prices.length === 0 ? (
            <div className="flex justify-center items-center py-12">
              <div className="text-center">
                <RefreshCw className="h-8 w-8 animate-spin text-indigo-600 mx-auto mb-4" />
                <p className="text-gray-600">
                  Fetching live prices from Vietnam...
                </p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="font-semibold">Chip</TableHead>
                    <TableHead className="font-semibold">
                      Configuration
                    </TableHead>
                    <TableHead className="text-right font-semibold">
                      Vietnam Price (VND)
                    </TableHead>
                    <TableHead className="text-right font-semibold">
                      India Price (INR)
                    </TableHead>
                    <TableHead className="text-right font-semibold">
                      VAT Refund (INR)
                    </TableHead>
                    <TableHead className="text-right font-semibold">
                      Final Price (INR)
                    </TableHead>
                    <TableHead className="text-right font-semibold">
                      Status
                    </TableHead>
                    <TableHead className="text-right font-semibold">
                      Buy
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPrices.length > 0 ? (
                    filteredPrices.map((item, index) => (
                      <TableRow key={index} className="hover:bg-gray-50">
                        <TableCell className="font-medium">
                          <Badge variant="outline" className="font-mono">
                            {item.category}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-gray-600 text-sm">
                          {item.configuration}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {item.vndPrice
                            ? formatCurrency(item.vndPrice, "VND")
                            : "N/A"}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {item.inrPrice
                            ? formatCurrency(item.inrPrice)
                            : "N/A"}
                        </TableCell>
                        <TableCell className="text-right font-mono text-green-600">
                          {item.vatRefund
                            ? formatCurrency(item.vatRefund)
                            : "N/A"}
                        </TableCell>
                        <TableCell className="text-right font-bold text-lg">
                          {item.finalPrice
                            ? formatCurrency(item.finalPrice)
                            : "N/A"}
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge
                            variant={item.available ? "default" : "secondary"}
                            className={
                              item.available
                                ? "bg-green-100 text-green-800"
                                : "bg-red-100 text-red-800"
                            }
                          >
                            {item.available ? "In Stock" : "Out of Stock"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Button
                              size="sm"
                              className="bg-indigo-600 hover:bg-indigo-700"
                            >
                              Visit
                            </Button>
                          </a>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={8}
                        className="text-center py-8 text-gray-500"
                      >
                        No models match the selected filter
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="container mx-auto max-w-7xl">
        <div className="text-center mb-8">
          <div className="flex justify-center items-center gap-2 mb-4">
            <Smartphone className="h-8 w-8 text-indigo-600" />
            <h1 className="text-4xl font-bold text-gray-900">
              VietMac Compare
            </h1>
          </div>
          <p className="text-lg text-gray-600 mb-4">
            Live MacBook Pro 16" prices from Vietnam's top Apple retailers for
            Indian tourists
          </p>
          <div className="flex justify-center items-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Globe className="h-4 w-4" />
              <span>4 Major Vietnamese Retailers</span>
            </div>
            <div className="flex items-center gap-1">
              <Calculator className="h-4 w-4" />
              <span>8.5% VAT Refund Included</span>
            </div>
          </div>
        </div>

        {exchangeRate && (
          <Card className="mb-6 bg-white/80 backdrop-blur-sm">
            <CardContent className="pt-6">
              <div className="flex justify-between items-center flex-wrap gap-4">
                <div className="text-sm text-gray-600">
                  Current Exchange Rate:{" "}
                  <span className="font-semibold">
                    1 INR = {exchangeRate.toFixed(4)} VND
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  {lastUpdate && (
                    <span className="text-xs text-gray-500">
                      Last updated: {lastUpdate}
                    </span>
                  )}
                  <Button
                    onClick={fetchPrices}
                    disabled={loading}
                    size="sm"
                    className="bg-indigo-600 hover:bg-indigo-700"
                  >
                    <RefreshCw
                      className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
                    />
                    Refresh Prices
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Filter and Sort Controls */}
        <Card className="mb-6 bg-white/80 backdrop-blur-sm">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              {/* Category Filter */}
              <div className="flex flex-col gap-2 w-full md:w-auto">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                  <Filter className="h-4 w-4" />
                  <span>Filter by Chip:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <Button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      size="sm"
                      variant={
                        selectedCategory === category ? "default" : "outline"
                      }
                      className={
                        selectedCategory === category
                          ? "bg-indigo-600 hover:bg-indigo-700"
                          : ""
                      }
                    >
                      {category}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Price Sort */}
              <div className="flex flex-col gap-2 w-full md:w-auto">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                  <ArrowUpDown className="h-4 w-4" />
                  <span>Sort by Price:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => setSortOrder("default")}
                    size="sm"
                    variant={sortOrder === "default" ? "default" : "outline"}
                    className={
                      sortOrder === "default"
                        ? "bg-indigo-600 hover:bg-indigo-700"
                        : ""
                    }
                  >
                    Default
                  </Button>
                  <Button
                    onClick={() => setSortOrder("low-to-high")}
                    size="sm"
                    variant={
                      sortOrder === "low-to-high" ? "default" : "outline"
                    }
                    className={
                      sortOrder === "low-to-high"
                        ? "bg-indigo-600 hover:bg-indigo-700"
                        : ""
                    }
                  >
                    Low to High
                  </Button>
                  <Button
                    onClick={() => setSortOrder("high-to-low")}
                    size="sm"
                    variant={
                      sortOrder === "high-to-low" ? "default" : "outline"
                    }
                    className={
                      sortOrder === "high-to-low"
                        ? "bg-indigo-600 hover:bg-indigo-700"
                        : ""
                    }
                  >
                    High to Low
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {renderPriceTable(
          marketplaceData.fptShop,
          "FPT Shop - Vietnam's Largest Electronics Retailer",
        )}
        {renderPriceTable(
          marketplaceData.shopDunk,
          "ShopDunk - Apple Premium Reseller",
        )}
        {renderPriceTable(
          marketplaceData.topZone,
          "TopZone - FPT's Premium Apple Store",
        )}
        {renderPriceTable(
          marketplaceData.cellphones,
          "CellphoneS - Major Electronics Chain",
        )}

        <Card className="mt-8 bg-white/90 backdrop-blur-sm shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl text-gray-900">
              Tracked MacBook Pro Models
            </CardTitle>
            <CardDescription className="text-gray-600">
              Base and Top configurations for each chip variant
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">M4 Chip</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Base: 10-core CPU, 10-core GPU, 16GB, 512GB</li>
                  <li>• Top: 10-core CPU, 10-core GPU, 24GB, 1TB</li>
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">M4 Pro Chip</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Base: 14-core CPU, 20-core GPU, 24GB, 512GB</li>
                  <li>• Top: 14-core CPU, 20-core GPU, 48GB, 1TB</li>
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">M4 Max Chip</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Base: 14-core CPU, 32-core GPU, 36GB, 1TB</li>
                  <li>• Top: 16-core CPU, 40-core GPU, 128GB, 2TB</li>
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">M3 Max Chip</h3>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Base: 14-core CPU, 30-core GPU, 36GB, 1TB</li>
                  <li>• Top: 16-core CPU, 40-core GPU, 128GB, 2TB</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-3 gap-6 mt-8">
          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Calculator className="h-5 w-5 text-indigo-600" />
                VAT Refund Info
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              <p>
                Vietnam VAT on electronics is 10%, but effective tourist refund
                is ~8.5% after airport processing fees. Minimum purchase: 2M
                VND.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Globe className="h-5 w-5 text-green-600" />
                Why Buy in Vietnam?
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              <p>
                Vietnam offers competitive MacBook pricing compared to India.
                All products come with official Apple warranty valid worldwide.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <Smartphone className="h-5 w-5 text-blue-600" />
                Live Updates
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-600">
              <p>
                Prices and exchange rates are updated in real-time from
                Vietnamese retailers. Click refresh for the latest data.
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="text-center mt-8 text-sm text-gray-500">
          <p>
            Prices scraped from official Vietnamese retailers (October 2025).
            Always verify final prices at the store. Bring your passport for VAT
            refund.
          </p>
        </div>
      </div>
    </div>
  );
}
