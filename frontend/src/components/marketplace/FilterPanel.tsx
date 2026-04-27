import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Search } from "lucide-react";
import { motion } from "framer-motion";
import { useContext } from "react";
import { FilterContext } from "@/pages/MarketplacePage";

export function FilterPanel() {
  const { filters, setFilters } = useContext(FilterContext);

  const handleSearchChange = (value: string) => {
    setFilters(prev => ({ ...prev, search: value }));
  };

  const handleCapacityChange = (capacity: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      capacities: checked 
        ? [...prev.capacities, capacity]
        : prev.capacities.filter(c => c !== capacity)
    }));
  };

  const handleRatingChange = (rating: string, checked: boolean) => {
    const ratingValue = parseFloat(rating.replace('-up', ''));
    setFilters(prev => ({
      ...prev,
      minRating: checked ? ratingValue : 0
    }));
  };

  const handlePaymentChange = (payment: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      paymentOptions: checked 
        ? [...prev.paymentOptions, payment]
        : prev.paymentOptions.filter(p => p !== payment)
    }));
  };

  const handleDeliveryTimeChange = (value: number[]) => {
    setFilters(prev => ({ ...prev, maxDeliveryTime: value[0] }));
  };

  const handleSortChange = (value: string) => {
    // Store sort option in filters for now, will be handled in parent component
    setFilters(prev => ({ ...prev, sortBy: value }));
  };

  return (
    <motion.div 
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="space-y-6"
    >
      <Card className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-primary/10 opacity-30"></div>
        
        <CardHeader className="relative z-10">
          <CardTitle className="text-lg flex items-center space-x-2">
            <span className="text-xl">🔍</span>
            <span>Filters & Sort</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">Refine your search results</p>
        </CardHeader>
        <CardContent className="space-y-6 relative z-10">
          <div className="space-y-2">
            <Label htmlFor="supplier-search">Search by Supplier</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input 
                id="supplier-search"
                placeholder="e.g., HydroServe" 
                className="pl-10"
                value={filters.search}
                onChange={(e) => handleSearchChange(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-3">
            <Label className="text-sm font-medium">Capacity</Label>
            <div className="space-y-3">
              {[
                { id: "500L", label: "500L" },
                { id: "800L", label: "800L" },
                { id: "1000L", label: "1000L" },
                { id: "1200L", label: "1200L" },
                { id: "1500L", label: "1500L" },
              ].map((capacity) => (
                <div key={capacity.id} className="flex items-center space-x-2">
                  <Checkbox 
                    id={capacity.id} 
                    checked={filters.capacities.includes(capacity.id)}
                    onCheckedChange={(checked) => handleCapacityChange(capacity.id, checked as boolean)}
                  />
                  <Label htmlFor={capacity.id} className="text-sm">
                    {capacity.label}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label className="text-sm font-medium">Rating</Label>
            <div className="space-y-3">
              {[
                { id: "4.5-up", label: "4.5 Stars & Up" },
                { id: "4-up", label: "4 Stars & Up" },
                { id: "3.5-up", label: "3.5 Stars & Up" },
              ].map((rating) => (
                <div key={rating.id} className="flex items-center space-x-2">
                  <Checkbox 
                    id={rating.id} 
                    checked={filters.minRating >= parseFloat(rating.id.replace('-up', ''))}
                    onCheckedChange={(checked) => handleRatingChange(rating.id, checked as boolean)}
                  />
                  <Label htmlFor={rating.id} className="text-sm">
                    {rating.label}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label className="text-sm font-medium">Payment Options</Label>
            <div className="space-y-3">
              {[
                { id: "upi", label: "UPI" },
                { id: "card", label: "Card Payment" },
                { id: "banking", label: "Net Banking" },
                { id: "cod", label: "Cash on Delivery" },
              ].map((payment) => (
                <div key={payment.id} className="flex items-center space-x-2">
                  <Checkbox 
                    id={payment.id} 
                    checked={filters.paymentOptions.includes(payment.id)}
                    onCheckedChange={(checked) => handlePaymentChange(payment.id, checked as boolean)}
                  />
                  <Label htmlFor={payment.id} className="text-sm">
                    {payment.label}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label className="text-sm font-medium">Max Delivery Time</Label>
            <div className="px-2">
              <Slider
                value={[filters.maxDeliveryTime]}
                onValueChange={handleDeliveryTimeChange}
                max={180}
                min={30}
                step={15}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>30 mins</span>
                <span>180 mins</span>
              </div>
              <div className="text-center text-sm text-muted-foreground mt-2">
                {filters.maxDeliveryTime} minutes
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="sort-by">Sort By</Label>
            <Select value={filters.sortBy || "rating-high"} onValueChange={handleSortChange}>
              <SelectTrigger>
                <SelectValue placeholder="Rating (High to Low)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rating-high">Rating (High to Low)</SelectItem>
                <SelectItem value="rating-low">Rating (Low to High)</SelectItem>
                <SelectItem value="price-low">Price (Low to High)</SelectItem>
                <SelectItem value="price-high">Price (High to Low)</SelectItem>
                <SelectItem value="delivery">Delivery Time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}