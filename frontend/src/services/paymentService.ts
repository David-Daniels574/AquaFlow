// src/services/paymentService.ts
export async function createPaymentIntent(amount: number, bookingId: string) {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5001";
  const token = localStorage.getItem('authToken');
  
  if (!token) {
    throw new Error("Authentication required. Please login.");
  }

  const res = await fetch(`${API_BASE_URL}/bookings/create-payment-intent`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({
      amount,
      booking_id: bookingId
    })
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.error || "Failed to create payment intent");
  }

  return res.json(); // { clientSecret }
}
