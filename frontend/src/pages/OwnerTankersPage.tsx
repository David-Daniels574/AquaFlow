import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  useOwnerCreateTanker,
  useOwnerDeleteTanker,
  useOwnerTankers,
  useOwnerUpdateTankerStatus,
} from "@/hooks/useAPI";
import { useToast } from "@/hooks/use-toast";

const defaultForm = {
  vehicle_number: "",
  capacity: "",
  type: "Standard",
  price_per_liter: "",
  base_delivery_fee: "",
  service_areas: "",
  images: "",
  amenities: "",
  description: "",
  emergency_contact: "",
  area: "",
  city: "",
};

export default function OwnerTankersPage() {
  const { toast } = useToast();
  const { data: tankers, isLoading } = useOwnerTankers();
  const createMutation = useOwnerCreateTanker();
  const deleteMutation = useOwnerDeleteTanker();
  const statusMutation = useOwnerUpdateTankerStatus();

  const [form, setForm] = useState(defaultForm);

  const tankersCount = useMemo(() => tankers?.length || 0, [tankers]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.vehicle_number || !form.capacity || !form.price_per_liter) {
      toast({
        title: "Missing required fields",
        description: "Vehicle number, capacity and price per liter are required.",
        variant: "destructive",
      });
      return;
    }

    try {
      await createMutation.mutateAsync({
        vehicle_number: form.vehicle_number,
        capacity: Number(form.capacity),
        type: form.type,
        price_per_liter: Number(form.price_per_liter),
        base_delivery_fee: Number(form.base_delivery_fee || 0),
        service_areas: form.service_areas
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        images: form.images
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        amenities: form.amenities
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        description: form.description,
        emergency_contact: form.emergency_contact,
        area: form.area,
        city: form.city,
      });

      setForm(defaultForm);
      toast({ title: "Tanker added", description: "Your tanker listing is live." });
    } catch (error: any) {
      toast({ title: "Failed to create tanker", description: error.message, variant: "destructive" });
    }
  };

  const onDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id);
      toast({ title: "Tanker removed" });
    } catch (error: any) {
      toast({ title: "Delete failed", description: error.message, variant: "destructive" });
    }
  };

  const onStatusChange = async (id: number, status: "available" | "booked" | "maintenance") => {
    try {
      await statusMutation.mutateAsync({ tankerId: id, status });
      toast({ title: "Status updated", description: `Tanker marked as ${status}.` });
    } catch (error: any) {
      toast({ title: "Status update failed", description: error.message, variant: "destructive" });
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl p-6 bg-gradient-to-r from-primary/15 to-primary/5">
        <h1 className="text-2xl font-bold">My Tankers</h1>
        <p className="text-muted-foreground">Manage listings, pricing, and availability.</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle>Add Tanker</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-3">
              <div>
                <Label>Vehicle Number*</Label>
                <Input value={form.vehicle_number} onChange={(e) => setForm((p) => ({ ...p, vehicle_number: e.target.value }))} />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label>Capacity (L)*</Label>
                  <Input type="number" value={form.capacity} onChange={(e) => setForm((p) => ({ ...p, capacity: e.target.value }))} />
                </div>
                <div>
                  <Label>Type</Label>
                  <Select value={form.type} onValueChange={(value) => setForm((p) => ({ ...p, type: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Standard">Standard</SelectItem>
                      <SelectItem value="Premium">Premium</SelectItem>
                      <SelectItem value="Emergency">Emergency</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label>Price/L*</Label>
                  <Input type="number" value={form.price_per_liter} onChange={(e) => setForm((p) => ({ ...p, price_per_liter: e.target.value }))} />
                </div>
                <div>
                  <Label>Base Fee</Label>
                  <Input type="number" value={form.base_delivery_fee} onChange={(e) => setForm((p) => ({ ...p, base_delivery_fee: e.target.value }))} />
                </div>
              </div>

              <div>
                <Label>Service Areas (comma-separated)</Label>
                <Input value={form.service_areas} onChange={(e) => setForm((p) => ({ ...p, service_areas: e.target.value }))} />
              </div>

              <div>
                <Label>Image URLs (comma-separated)</Label>
                <Input value={form.images} onChange={(e) => setForm((p) => ({ ...p, images: e.target.value }))} />
              </div>

              <div>
                <Label>Amenities (comma-separated)</Label>
                <Input value={form.amenities} onChange={(e) => setForm((p) => ({ ...p, amenities: e.target.value }))} />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label>Area</Label>
                  <Input value={form.area} onChange={(e) => setForm((p) => ({ ...p, area: e.target.value }))} />
                </div>
                <div>
                  <Label>City</Label>
                  <Input value={form.city} onChange={(e) => setForm((p) => ({ ...p, city: e.target.value }))} />
                </div>
              </div>

              <div>
                <Label>Emergency Contact</Label>
                <Input value={form.emergency_contact} onChange={(e) => setForm((p) => ({ ...p, emergency_contact: e.target.value }))} />
              </div>

              <div>
                <Label>Description</Label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  rows={3}
                />
              </div>

              <Button className="w-full" type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Adding..." : "Add Tanker"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Fleet Listings ({tankersCount})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading ? (
              <p className="text-muted-foreground">Loading tankers...</p>
            ) : !tankers?.length ? (
              <p className="text-muted-foreground">No tankers listed yet.</p>
            ) : (
              tankers.map((tanker) => (
                <div key={tanker.id} className="rounded-lg border p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                  <div>
                    <p className="font-semibold">{tanker.vehicle_number} • {tanker.type}</p>
                    <p className="text-sm text-muted-foreground">
                      {tanker.capacity}L • Rs {tanker.price_per_liter}/L • {tanker.area}, {tanker.city}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">Status: {tanker.status || "available"}</p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" variant="outline" onClick={() => onStatusChange(tanker.id, "available")}>Set Available</Button>
                    <Button size="sm" variant="outline" onClick={() => onStatusChange(tanker.id, "maintenance")}>Maintenance</Button>
                    <Button size="sm" variant="destructive" onClick={() => onDelete(tanker.id)} disabled={deleteMutation.isPending}>
                      Delete
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
