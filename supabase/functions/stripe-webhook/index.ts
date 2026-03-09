// Supabase Edge Function — Stripe Webhook Handler
// Listens for Stripe subscription events and updates user_profiles accordingly.
//
// Deploy: supabase functions deploy stripe-webhook --no-verify-jwt
// Set secrets:
//   supabase secrets set STRIPE_SECRET_KEY=sk_live_xxx
//   supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_xxx

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import Stripe from "https://esm.sh/stripe@13.10.0?target=deno";

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") ?? "", {
  apiVersion: "2023-10-16",
  httpClient: Stripe.createFetchHttpClient(),
});

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const WEBHOOK_SECRET = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";

// Plan mapping from Stripe Price IDs
const PRICE_TO_PLAN: Record<string, string> = {
  [Deno.env.get("STRIPE_PRICE_PRO") ?? "price_xxx_pro"]: "pro",
  [Deno.env.get("STRIPE_PRICE_TEAM") ?? "price_xxx_team"]: "team",
};

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", {
      headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "stripe-signature, content-type" },
    });
  }

  try {
    const body = await req.text();
    const signature = req.headers.get("stripe-signature");

    if (!signature) {
      return new Response("Missing stripe-signature header", { status: 400 });
    }

    // Verify webhook signature
    let event: Stripe.Event;
    try {
      event = stripe.webhooks.constructEvent(body, signature, WEBHOOK_SECRET);
    } catch (err) {
      console.error("Webhook signature verification failed:", err);
      return new Response(`Webhook Error: ${err}`, { status: 400 });
    }

    // Initialize Supabase admin client (bypasses RLS)
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

    console.log(`Processing event: ${event.type}`);

    switch (event.type) {
      // ─── Subscription Created ─────────────────────────────────────────
      case "customer.subscription.created":
      case "customer.subscription.updated": {
        const subscription = event.data.object as Stripe.Subscription;
        const customerId = subscription.customer as string;
        const status = subscription.status; // active, past_due, canceled, etc.
        const priceId = subscription.items.data[0]?.price?.id ?? "";
        const plan = PRICE_TO_PLAN[priceId] ?? "pro";

        const isActive = status === "active" || status === "trialing";
        const expiresAt = new Date(subscription.current_period_end * 1000).toISOString();

        // Find user by stripe_customer_id
        const { data: profiles, error: findError } = await supabase
          .from("user_profiles")
          .select("user_id")
          .eq("stripe_customer_id", customerId);

        if (findError || !profiles?.length) {
          // Try metadata fallback
          const userId = subscription.metadata?.user_id;
          if (userId) {
            await supabase.from("user_profiles").update({
              subscription_plan: plan,
              subscription_active: isActive,
              subscription_expires_at: expiresAt,
              stripe_customer_id: customerId,
            }).eq("user_id", userId);
            console.log(`Updated user ${userId} → plan=${plan}, active=${isActive}`);
          } else {
            console.error(`No user found for customer ${customerId}`);
          }
        } else {
          const userId = profiles[0].user_id;
          await supabase.from("user_profiles").update({
            subscription_plan: plan,
            subscription_active: isActive,
            subscription_expires_at: expiresAt,
          }).eq("user_id", userId);
          console.log(`Updated user ${userId} → plan=${plan}, active=${isActive}`);
        }
        break;
      }

      // ─── Subscription Deleted (Canceled) ──────────────────────────────
      case "customer.subscription.deleted": {
        const subscription = event.data.object as Stripe.Subscription;
        const customerId = subscription.customer as string;

        const { data: profiles } = await supabase
          .from("user_profiles")
          .select("user_id")
          .eq("stripe_customer_id", customerId);

        if (profiles?.length) {
          const userId = profiles[0].user_id;
          await supabase.from("user_profiles").update({
            subscription_plan: "free",
            subscription_active: false,
            subscription_expires_at: null,
          }).eq("user_id", userId);
          console.log(`Subscription canceled for user ${userId} → free plan`);
        }
        break;
      }

      // ─── Invoice Payment Failed ───────────────────────────────────────
      case "invoice.payment_failed": {
        const invoice = event.data.object as Stripe.Invoice;
        const customerId = invoice.customer as string;

        const { data: profiles } = await supabase
          .from("user_profiles")
          .select("user_id")
          .eq("stripe_customer_id", customerId);

        if (profiles?.length) {
          const userId = profiles[0].user_id;
          await supabase.from("user_profiles").update({
            subscription_active: false,
          }).eq("user_id", userId);
          console.log(`Payment failed for user ${userId}, subscription deactivated`);
        }
        break;
      }

      // ─── Checkout Completed ───────────────────────────────────────────
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        const userId = session.metadata?.user_id;
        const plan = session.metadata?.plan;
        const customerId = session.customer as string;

        if (userId && plan) {
          await supabase.from("user_profiles").update({
            subscription_plan: plan,
            subscription_active: true,
            stripe_customer_id: customerId,
          }).eq("user_id", userId);
          console.log(`Checkout completed: user ${userId} → plan=${plan}`);
        }
        break;
      }

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("Webhook processing error:", err);
    return new Response(`Server Error: ${err}`, { status: 500 });
  }
});
