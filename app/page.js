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
import { RefreshCw, Smartphone, Globe, Calculator, Store } from "lucide-react";
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

  const renderPriceTable = (prices, marketplaceName) => (
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
                  <TableHead className="font-semibold">Model</TableHead>
                  <TableHead className="font-semibold">Configuration</TableHead>
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
                    Buy Now
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {prices.length > 0 ? (
                  prices.map((item, index) => (
                    <TableRow key={index} className="hover:bg-gray-50">
                      <TableCell className="font-medium">
                        {item.model}
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {item.configuration}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.vndPrice
                          ? formatCurrency(item.vndPrice, "VND")
                          : "N/A"}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.inrPrice ? formatCurrency(item.inrPrice) : "N/A"}
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
                            Visit Store
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
                      No price data available. Click refresh to fetch latest
                      prices.
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
              <div className="flex justify-between items-center">
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
              Official Apple Resellers in Vietnam
            </CardTitle>
            <CardDescription className="text-gray-600">
              All stores offer VAT refund for tourists with valid documentation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">Hanoi Locations</h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• F.Studio by FPT - 269 P. Chùa Bộc, Đống Đa</li>
                  <li>• ShopDunk - 76 Thái Hà, Đống Đa</li>
                  <li>• TopZone - 291 Nguyen Van Cu, Long Bien</li>
                  <li>• CellphoneS - 21 Thai Ha, Dong Da</li>
                </ul>
              </div>
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-2">
                  Ho Chi Minh City Locations
                </h3>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• F.Studio - Multiple locations across districts</li>
                  <li>• ShopDunk - District 1, 3, and Binh Thanh</li>
                  <li>• TopZone - District 1 and Tan Binh</li>
                  <li>• CellphoneS - District 1 and 10</li>
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
                Prices and exchange rates are updated in real-time. Refresh for
                the most current information before purchasing.
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="text-center mt-8 text-sm text-gray-500">
          <p>
            Prices are from official Vietnamese retailers (October 2025). Always
            verify final prices at the store. Bring your passport for VAT
            refund.
          </p>
        </div>
      </div>
    </div>
  );
}
