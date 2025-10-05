"use client";

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
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useState } from "react";

const allColumns = [
  "Shop",
  "Model",
  "Configuration",
  "Category",
  "VND Price",
  "INR Price",
  "VAT Refund",
  "Final Price",
] as const;

function MacBookPricesTable({ data }) {
  const [visibleColumns, setVisibleColumns] = useState([...allColumns]);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [shopFilter, setShopFilter] = useState("");

  const filteredData = data.filter((item) => {
    return (
      (!categoryFilter || item.category.toLowerCase().includes(categoryFilter.toLowerCase())) &&
      (!shopFilter || item.shop.toLowerCase().includes(shopFilter.toLowerCase()))
    );
  });

  const toggleColumn = (col) => {
    setVisibleColumns((prev) =>
      prev.includes(col)
        ? prev.filter((c) => c !== col)
        : [...prev, col]
    );
  };

  return (
    <div className="container my-10 space-y-4 p-4 border border-border rounded-lg bg-background shadow-sm overflow-x-auto">
      <div className="flex flex-wrap gap-4 items-center justify-between mb-6">
        <div className="flex gap-2 flex-wrap">
          <Input
            placeholder="Filter by shop..."
            value={shopFilter}
            onChange={(e) => setShopFilter(e.target.value)}
            className="w-48"
          />
          <Input
            placeholder="Filter by category..."
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-48"
          />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              Columns
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-48">
            {allColumns.map((col) => (
              <DropdownMenuCheckboxItem
                key={col}
                checked={visibleColumns.includes(col)}
                onCheckedChange={() => toggleColumn(col)}
              >
                {col}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Table className="w-full">
        <TableHeader>
          <TableRow>
            {visibleColumns.includes("Shop") && <TableHead className="w-[150px]">Shop</TableHead>}
            {visibleColumns.includes("Model") && <TableHead className="w-[180px]">Model</TableHead>}
            {visibleColumns.includes("Configuration") && <TableHead className="w-[300px]">Configuration</TableHead>}
            {visibleColumns.includes("Category") && <TableHead className="w-[120px]">Category</TableHead>}
            {visibleColumns.includes("VND Price") && <TableHead className="w-[130px]">VND Price</TableHead>}
            {visibleColumns.includes("INR Price") && <TableHead className="w-[130px]">INR Price</TableHead>}
            {visibleColumns.includes("VAT Refund") && <TableHead className="w-[130px]">VAT Refund</TableHead>}
            {visibleColumns.includes("Final Price") && <TableHead className="w-[130px]">Final Price</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredData.length ? (
            filteredData.map((item, idx) => (
              <TableRow key={`${item.shop}-${item.id}-${idx}`}>
                {visibleColumns.includes("Shop") && (
                  <TableCell className="font-medium whitespace-nowrap">
                    <Badge
                      className={cn(
                        "whitespace-nowrap",
                        item.shop === "FPT Shop" && "bg-blue-500 text-white",
                        item.shop === "ShopDunk" && "bg-purple-500 text-white",
                        item.shop === "TopZone" && "bg-green-500 text-white",
                        item.shop === "CellphoneS" && "bg-orange-500 text-white",
                      )}
                    >
                      {item.shop}
                    </Badge>
                  </TableCell>
                )}
                {visibleColumns.includes("Model") && (
                  <TableCell className="font-medium whitespace-nowrap">{item.model}</TableCell>
                )}
                {visibleColumns.includes("Configuration") && (
                  <TableCell className="whitespace-nowrap text-xs">{item.configuration}</TableCell>
                )}
                {visibleColumns.includes("Category") && (
                  <TableCell className="whitespace-nowrap">
                    <Badge variant="outline">{item.category}</Badge>
                  </TableCell>
                )}
                {visibleColumns.includes("VND Price") && (
                  <TableCell className="whitespace-nowrap">
                    ₫{item.vndPrice?.toLocaleString() || "N/A"}
                  </TableCell>
                )}
                {visibleColumns.includes("INR Price") && (
                  <TableCell className="whitespace-nowrap">
                    ₹{item.inrPrice?.toLocaleString() || "N/A"}
                  </TableCell>
                )}
                {visibleColumns.includes("VAT Refund") && (
                  <TableCell className="whitespace-nowrap text-green-600">
                    -₹{item.vatRefund?.toLocaleString() || "N/A"}
                  </TableCell>
                )}
                {visibleColumns.includes("Final Price") && (
                  <TableCell className="whitespace-nowrap font-bold text-primary">
                    ₹{item.finalPrice?.toLocaleString() || "N/A"}
                  </TableCell>
                )}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={visibleColumns.length} className="text-center py-6">
                No results found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export default MacBookPricesTable;
