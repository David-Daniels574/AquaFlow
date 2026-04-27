import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Star, MapPin, Clock } from "lucide-react";
import { motion } from "framer-motion";
import { useContext } from "react";
import { FilterContext } from "@/pages/MarketplacePage";
import tankerImg from "./s-1.png"; 
import tankerIms from "./s-2.png";
import tankerImt from "./s-3.png";
import tankerImu from "./s-4.png";
import tankerImv from "./s-5.png";
import tankerImz from "./s-6.png";
import { Supplier } from "@/services/api";

// Map supplier IDs to images for fallback
const supplierImages = [tankerImg, tankerIms, tankerImt, tankerImu, tankerImv, tankerImz];
interface TankerGridProps {
  allSuppliers: Supplier[];
  isLoading: boolean;
  error: unknown;
  onBookNow: (supplier: Supplier) => void;
}

export function TankerGrid({ allSuppliers, isLoading, error, onBookNow }: TankerGridProps) {
  const { filteredSuppliers } = useContext(FilterContext);
  
  // Use filtered suppliers if they exist, otherwise use all suppliers
  const suppliers = filteredSuppliers.length > 0 ? filteredSuppliers : (allSuppliers || []);
  if (isLoading) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Loading Water Tankers...</h2>
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, index) => (
            <div key={index} className="h-80 bg-gray-200 animate-pulse rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Error Loading Tankers</h2>
        <p className="text-red-500">Failed to load tanker data. Please try again later.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Showing {suppliers?.length || 0} Water Tankers Available</h2>
      
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {suppliers?.map((supplier, index) => (
          <motion.div
            key={supplier.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="overflow-hidden hover:shadow-lg transition-shadow">
              <div className="relative">
                <img 
                  src={supplier.photo_url || supplierImages[index % supplierImages.length]} 
                  alt={supplier.name}
                  className="w-full h-32 object-cover"
                />
                <Badge 
                  variant="secondary" 
                  className={`absolute top-2 left-2 text-white ${supplier.is_available ? "bg-status-success" : "bg-red-500"}`}
                >
                  {supplier.is_available ? "Available" : "Not Available"}
                </Badge>
                <Badge
                  variant="outline"
                  className="absolute top-2 right-2 bg-white"
                >
                  {supplier.offers?.[0]?.quantity ? `${supplier.offers[0].quantity}L` : '500L'}
                </Badge>
              </div>
              
              <CardContent className="p-4 space-y-3">
                <div>
                  <h3 className="font-semibold text-lg">{supplier.name}</h3>
                  <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span>{supplier.rating}</span>
                    <span>({supplier.num_reviews} reviews)</span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                  <MapPin className="h-4 w-4" />
                  <span>{supplier.area}, {supplier.city}</span>
                </div>
                
                <div className="flex flex-wrap gap-1">
                  {supplier.offers?.map((offer) => (
                    <Badge key={offer.quantity} variant="outline" className="text-xs">
                      {offer.quantity}L
                    </Badge>
                  ))}
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-lg font-semibold">₹ Starts from ₹{supplier.starting_from || supplier.offers?.[0]?.cost || 'N/A'}</span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>Est {supplier.estimated_eta ? `${supplier.estimated_eta} mins` : '30-45 mins'}</span>
                </div>
                
                <Button 
                  className="w-full bg-primary hover:bg-primary-hover"
                  disabled={!supplier.is_available}
                  onClick={() => onBookNow(supplier)}
                >
                  {supplier.is_available ? "Book Now" : "Unavailable"}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}