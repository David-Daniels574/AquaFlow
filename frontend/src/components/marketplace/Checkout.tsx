import { CardElement, useStripe, useElements } from "@stripe/react-stripe-js";
import { createPaymentIntent } from "../../services/paymentService";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, XCircle, Droplet } from "lucide-react";
import { Supplier } from "@/services/api";
import { useCreateMarketplaceBooking } from "@/hooks/useAPI";
import { useToast } from "@/components/ui/use-toast";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface Props {
  bookingId: string;
  supplier: Supplier;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function Checkout({ bookingId, supplier, onSuccess, onCancel }: Props) {
  const stripe = useStripe();
  const elements = useElements();
  const createBookingMutation = useCreateMarketplaceBooking();
  const { toast } = useToast();
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState<{ quantity: number; cost: number } | null>(null);

  // Set default selected offer
  useEffect(() => {
    if (supplier.offers && supplier.offers.length > 0) {
      setSelectedOffer(supplier.offers[0]);
    }
  }, [supplier]);

  const handlePayment = async () => {
    if (!stripe || !elements) {
      setError("Stripe is not loaded yet. Please try again.");
      return;
    }

    if (!selectedOffer) {
      setError("Please select a tanker capacity.");
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      console.log("Step 1: Creating payment intent for amount:", selectedOffer.cost);
      // Step 1: Create payment intent
      const { clientSecret } = await createPaymentIntent(selectedOffer.cost, bookingId);
      console.log("Step 2: Payment intent created, confirming card payment");

      // Step 2: Confirm card payment
      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: elements.getElement(CardElement)!
        }
      });

      if (result.error) {
        console.error("Payment error:", result.error);
        setError(result.error.message || "Payment failed");
        setProcessing(false);
      } else if (result.paymentIntent?.status === "succeeded") {
        console.log("Step 3: Payment succeeded, creating booking");
        // Step 3: Create booking after successful payment
        try {
          console.log("Booking details:", {
            tanker_id: supplier.id,
            quantity: selectedOffer.quantity,
            total_amount: selectedOffer.cost
          });

          await createBookingMutation.mutateAsync({
            tanker_id: supplier.id,
            quantity: selectedOffer.quantity,
            total_amount: selectedOffer.cost,
            delivery_address: "Address to be shared after booking",
          });

          console.log("Step 4: Booking successful!");
          setSuccess(true);
          setProcessing(false);
          
          toast({
            title: "Payment & Booking Successful!",
            description: `Your ${selectedOffer.quantity}L water tanker from ${supplier.name} has been booked.`,
          });

          setTimeout(() => {
            onSuccess();
          }, 1500);
        } catch (bookingError: any) {
          console.error("Booking error:", bookingError);
          setError("Payment succeeded but booking failed. Please contact support.");
          setProcessing(false);
          toast({
            title: "Booking Error",
            description: "Payment was successful but there was an error creating the booking.",
            variant: "destructive"
          });
        }
      }
    } catch (err: any) {
      console.error("Payment flow error:", err);
      setError(err.message || "Payment failed. Please try again.");
      setProcessing(false);
      toast({
        title: "Payment Failed",
        description: err.message || "There was an error processing your payment.",
        variant: "destructive"
      });
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Complete Your Booking</CardTitle>
        <CardDescription>Select tanker capacity and enter payment details</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {success && (
          <Alert className="border-green-500 text-green-700">
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>Payment successful! Redirecting...</AlertDescription>
          </Alert>
        )}

        {/* Tanker Capacity Selection */}
        <div className="space-y-3">
          <Label className="text-base font-semibold">Select Tanker Capacity</Label>
          <RadioGroup
            value={selectedOffer ? `${selectedOffer.quantity}` : ""}
            onValueChange={(value) => {
              const offer = supplier.offers?.find(o => o.quantity === parseInt(value));
              if (offer) setSelectedOffer(offer);
            }}
            className="space-y-2"
          >
            {supplier.offers?.map((offer) => (
              <div
                key={offer.quantity}
                className={`flex items-center space-x-3 border rounded-lg p-4 cursor-pointer transition-all ${
                  selectedOffer?.quantity === offer.quantity
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
                onClick={() => setSelectedOffer(offer)}
              >
                <RadioGroupItem value={`${offer.quantity}`} id={`offer-${offer.quantity}`} />
                <Label
                  htmlFor={`offer-${offer.quantity}`}
                  className="flex-1 cursor-pointer flex items-center justify-between"
                >
                  <div className="flex items-center space-x-2">
                    <Droplet className="h-4 w-4 text-primary" />
                    <span className="font-semibold">{offer.quantity}L</span>
                  </div>
                  <span className="text-lg font-bold">₹{offer.cost}</span>
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        {/* Payment Section */}
        <div className="space-y-3 pt-2">
          <Label className="text-base font-semibold">Payment Details</Label>
          <div className="p-4 border rounded-md">
            <CardElement
              options={{
                style: {
                  base: {
                    fontSize: '16px',
                    color: '#424770',
                    '::placeholder': {
                      color: '#aab7c4',
                    },
                  },
                  invalid: {
                    color: '#9e2146',
                  },
                },
              }}
            />
          </div>
        </div>

        <div className="flex justify-between items-center pt-4 border-t">
          <div>
            <p className="text-sm text-muted-foreground">Total Amount</p>
            <p className="text-2xl font-bold">₹{selectedOffer?.cost || 0}</p>
          </div>
          <div className="space-x-2">
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={processing || success}
            >
              Cancel
            </Button>
            <Button
              onClick={handlePayment}
              disabled={!stripe || processing || success || !selectedOffer}
            >
              {processing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {processing ? "Processing..." : `Pay ₹${selectedOffer?.cost || 0}`}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
