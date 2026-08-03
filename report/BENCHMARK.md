# BENCHMARK (5 Queries)

1) Question: How can a Shopify merchant issue a refund for an order?
   Query Type: Process
   Gold Answer:
   "You can also issue refunds or cancel orders when needed."
   Gold Document: k4-shopify-returns
   Expected Chunk:
   "Order fulfillment is the workflow of processing, managing, and shipping customer orders from your Shopify store. After customers place orders, you can manage orders from the Orders page in your Shopify admin. This includes capturing payments, reviewing order details, printing shipping documents, and preparing items for fulfillment. You can also issue refunds or cancel orders when needed."
   Metadata Filter: {"customer_role":"buyer"}


2) Question: What payment methods can customers use on a Shopify store?
   Query Type: Listing
   Gold Answer: "Customers can pay using Shopify Payments, third-party providers (PayPal, Amazon Pay, Apple Pay), and accelerated checkouts."
   Gold Document: k4-shopify-payments
   Expected Chunk:
   "When a customer checks out, they can choose to pay using any methods activated in Payment providers. You can enable Shopify Payments, third-party providers (PayPal, Amazon Pay, Apple Pay), and accelerated checkouts. If you use Shopify Payments you can also enable Shop Pay for faster checkout."
   Metadata Filter: {"customer_role":"both"}


3) Question: What practices can lead to account suspension under Google Merchant Center policies?
   Query Type: Condition / Policy
   Gold Answer:
   "Disallowed practices include misrepresentation, hiding costs, unclear return/refund policies, and offering unavailable products. Violations can lead to account suspension."
   Gold Document: k4-google-merchant-policy
   Expected Chunk:
   "Google requires merchants to be upfront and provide all relevant information. Disallowed practices include misrepresentation, hiding costs, unclear return/refund policies, and offering unavailable products. Violations can lead to account suspension."
   Metadata Filter: {"customer_role":"seller"}


4) Question: What customer service practices does Shopify recommend?
   Query Type: Best Practices
   Gold Answer:
   "Setting clear store policies (shipping, returns, contact channels), offering multiple contact methods (chat, email, social), using tools like Shopify Inbox for messaging, and setting expectations with policies shown in Settings > Policies."
   Gold Document: k4-shopify-customer-service
   Expected Chunk:
   "Key practices include: setting clear store policies (shipping, returns, contact channels), offering multiple contact methods (chat, email, social), using tools like Shopify Inbox for messaging, and setting expectations with policies shown in Settings > Policies."
   Metadata Filter: {"customer_role":"both"}


5) Question: What should I know about return policies?
   Query Type: Metadata Filter (Buyer)
   Purpose:
   This query is intentionally ambiguous. Without metadata filtering, the retriever may return seller-oriented policy documents (e.g., Google Merchant Center) instead of buyer-oriented return information. Applying the metadata filter ensures retrieval from the correct document.
   Gold Answer:
   "Sellers must follow eBay rules and buyers can request returns according to the stated policies."
   Gold Document: k4-ebay-return-policy
   Expected Chunk:
   "eBay documents include details about what personal data is shared in transactions, seller/buyer responsibilities, and how returns and refunds are managed via the platform. Sellers must follow eBay rules and buyers can request returns according to the stated policies."
   Metadata Filter: {"customer_role":"buyer"}