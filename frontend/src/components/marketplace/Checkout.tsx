import { CardElement, useStripe, useElements } from "@stripe/react-stripe-js";
import { createPaymentIntent } from "../../services/paymentService";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Supplier } from "@/services/api";
import { useBookTanker } from "@/hooks/useAPI";
import { useToast } from "@/components/ui/use-toast";

interface Props {
  amount: number;
  bookingId: string;
  supplier: Supplier;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function Checkout({ amount, bookingId, supplier, onSuccess, onCancel }: Props) {
  const stripe = useStripe();
  const elements = useElements();
  const bookTankerMutation = useBookTanker();
  const { toast } = useToast();
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handlePayment = async () => {
    if (!stripe || !elements) {
      setError("Stripe is not loaded yet. Please try again.");
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      console.log("Step 1: Creating payment intent for amount:", amount);
      // Step 1: Create payment intent
      const { clientSecret } = await createPaymentIntent(amount, bookingId);
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
          const offer = supplier.offers && supplier.offers.length > 0 
            ? supplier.offers[0] 
            : { quantity: 500, cost: supplier.starting_from || amount };
          
          console.log("Booking details:", {
            supplier_id: supplier.id,
            volume: offer.quantity,
            price: amount
          });

          await bookTankerMutation.mutateAsync({
            supplier_id: supplier.id,
            volume: offer.quantity,
            price: amount
          });

          console.log("Step 4: Booking successful!");
          setSuccess(true);
          setProcessing(false);
          
          toast({
            title: "Payment & Booking Successful!",
            description: `Your water tanker from ${supplier.name} has been booked.`,
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
        <CardTitle>Complete Payment</CardTitle>
        <CardDescription>Enter your card details to complete the booking</CardDescription>
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

        <div className="flex justify-between items-center pt-4">
          <div className="text-2xl font-bold">₹{amount}</div>
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
              disabled={!stripe || processing || success}
            >
              {processing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {processing ? "Processing..." : `Pay ₹${amount}`}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
