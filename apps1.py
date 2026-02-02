# import streamlit as st
# import pandas as pd
# import requests
# import json
# import os
# import re
# from dotenv import load_dotenv
# from urllib.parse import quote_plus
# from sqlalchemy import create_engine, text
# from datetime import datetime
# from openai import OpenAI


# # =========================
# # LOAD ENV
# # =========================
# load_dotenv()

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# CRM_URL = os.getenv("CRM_URL")

# DB_USER = os.getenv("DB_USER")
# DB_PASS_RAW = os.getenv("DB_PASSWORD")
# DB_PASS = quote_plus(DB_PASS_RAW)
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = os.getenv("DB_PORT", "3306")
# DB_NAME = os.getenv("DB_NAME")

# # =========================
# # PAGE CONFIG
# # =========================
# st.set_page_config(page_title="CRM GST Invoice – WhatsApp Chatbot", layout="wide")

# # =========================
# # DB ENGINE
# # =========================
# ENGINE = create_engine(
#     f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
#     pool_pre_ping=True
# )

# # =========================
# # INITIALIZE OPENAI CLIENT
# # =========================
# if OPENAI_API_KEY and OPENAI_API_KEY != "skip_ai":
#     client = OpenAI(api_key=OPENAI_API_KEY)
# else:
#     client = None

# # =========================
# # SESSION STATE
# # =========================
# defaults = {
#     "messages": [],
#     "chat_stage": None,
#     "pending_data": {},
#     "invoice": [],
#     "invoice_flow": None,
#     "invoice_meta": {
#         "project_id": None,
#         "project_name": None,
#         "party_id": None,
#         "party_name": None,
#         "party_address": None,
#         "party_pincode": None,
#         "party_gst": None,
#         "invoice_type": None,
#         "invoice_no": None,
#         "invoice_date": None,
#         "total_amount": 0,
#         "gst_percentage": 18,
#         "cgst": 0,
#         "sgst": 0,
#         "igst": 0,
#         "grand_total": 0,
#         "invoice_prefix": None,
#         "invoice_sequence": None
#     },
#     "awaiting_choice": False,
#     "choice_type": None,
#     "choice_options": [],
#     "product_flow": None,
#     "temp_product": {},
#     "ai_context": [],
#     "viewing_old_invoice": False,
#     "old_invoice_data": None,
#     "stock_alert": [],
#     "product_suggestions": [],
#     "last_product_search": ""
# }

# for k, v in defaults.items():
#     if k not in st.session_state:
#         st.session_state[k] = v




# # =========================
# # GST CALCULATION FUNCTIONS
# # =========================

# def get_gst_rate_from_pincode(pincode):
#     """Determine GST rate based on pincode"""
#     if not pincode:
#         return {
#             "type": "CGST+SGST",
#             "cgst_rate": 9,
#             "sgst_rate": 9,
#             "igst_rate": 0,
#             "total_gst_rate": 18
#         }
    
#     # Extract only digits from pincode
#     pincode_str = re.sub(r'\D', '', str(pincode))
    
#     # Check if we have at least 6 digits
#     if len(pincode_str) >= 6:
#         first_two = pincode_str[:2]
        
#         # Tamil Nadu pincodes start with 60-64
#         if first_two in ['60', '61', '62', '63', '64']:
#             return {
#                 "type": "CGST+SGST",
#                 "cgst_rate": 9,
#                 "sgst_rate": 9,
#                 "igst_rate": 0,
#                 "total_gst_rate": 18
#             }
    
#     # Default to IGST for other states
#     return {
#         "type": "IGST",
#         "cgst_rate": 0,
#         "sgst_rate": 0,
#         "igst_rate": 18,
#         "total_gst_rate": 18
#     }

# def calculate_gst_breakdown(subtotal, pincode=None, party_state=None):
#     """Calculate GST breakdown"""
#     if not subtotal or subtotal <= 0:
#         return {
#             "subtotal": 0,
#             "cgst_amount": 0,
#             "sgst_amount": 0,
#             "igst_amount": 0,
#             "total_gst": 0,
#             "grand_total": 0,
#             "gst_type": "Not Calculated",
#             "cgst_rate": 0,
#             "sgst_rate": 0,
#             "igst_rate": 0
#         }
    
#     gst_info = get_gst_rate_from_pincode(pincode)
    
#     if gst_info["type"] == "CGST+SGST":
#         cgst_amount = (subtotal * gst_info["cgst_rate"]) / 100
#         sgst_amount = (subtotal * gst_info["sgst_rate"]) / 100
#         igst_amount = 0
#     else:
#         cgst_amount = 0
#         sgst_amount = 0
#         igst_amount = (subtotal * gst_info["igst_rate"]) / 100
    
#     total_gst = cgst_amount + sgst_amount + igst_amount
#     grand_total = subtotal + total_gst
    
#     return {
#         "subtotal": subtotal,
#         "cgst_amount": round(cgst_amount, 2),
#         "sgst_amount": round(sgst_amount, 2),
#         "igst_amount": round(igst_amount, 2),
#         "total_gst": round(total_gst, 2),
#         "grand_total": round(grand_total, 2),
#         "gst_type": gst_info["type"],
#         "cgst_rate": gst_info["cgst_rate"],
#         "sgst_rate": gst_info["sgst_rate"],
#         "igst_rate": gst_info["igst_rate"]
#     }

# def get_product_suggestions(search_term):
#     """Get product suggestions from database based on search term"""
#     if not search_term or len(search_term) < 2:
#         return []
    
#     try:
#         with ENGINE.connect() as conn:
#             query = text("""
#                 SELECT DISTINCT item_description 
#                 FROM boq_items 
#                 WHERE LOWER(item_description) LIKE :pattern
#                 ORDER BY item_description
#                 LIMIT 10
#             """)
#             result = conn.execute(query, {"pattern": f"%{search_term.lower()}%"}).fetchall()
#             return [row[0] for row in result]
#     except Exception as e:
#         print(f"Error getting product suggestions: {e}")
#         return []
    

#     # =========================
#     # DATABASE FUNCTIONS - STOCK MANAGEMENT
#     # =========================

# def get_projects():
#     """Fetch all projects from database"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("SELECT id, project_name FROM projects ORDER BY project_name")
#             result = conn.execute(query)
#             projects = [(row[0], row[1]) for row in result.fetchall()]
#             return projects
#     except Exception as e:
#         return []

# def get_parties():
#     """Fetch all parties from database with address, pincode, GST"""
#     try:
#         with ENGINE.connect() as conn:
#             # First get column names
#             query = text("SHOW COLUMNS FROM parties")
#             result = conn.execute(query)
#             columns = [row[0] for row in result.fetchall()]
            
#             # Build query based on available columns
#             select_cols = ["id"]
            
#             # Find name column
#             name_cols = ["party_name", "name", "company_name", "customer_name", "vendor_name", "client_name"]
#             name_col = None
#             for col in name_cols:
#                 if col in columns:
#                     select_cols.append(f"{col} as name")
#                     name_col = col
#                     break
            
#             if not name_col:
#                 select_cols.append("id as name")
            
#             # Add address columns if available
#             address_cols = ["address", "billingAddress", "billing_address", "party_address", "street", "city"]
#             for col in address_cols:
#                 if col in columns:
#                     select_cols.append(f"{col} as address")
#                     break
            
#             # Add pincode if available
#             pincode_cols = ["pincode", "pin_code", "postal_code", "zip_code"]
#             for col in pincode_cols:
#                 if col in columns:
#                     select_cols.append(f"{col} as pincode")
#                     break
            
#             # Add GST if available
#             gst_cols = ["gst_number", "gst", "gstin", "gst_no"]
#             for col in gst_cols:
#                 if col in columns:
#                     select_cols.append(f"{col} as gst")
#                     break
            
#             # Execute query
#             query = text(f"SELECT {', '.join(select_cols)} FROM parties ORDER BY name")
#             result = conn.execute(query)
            
#             # Process results
#             parties = []
#             for row in result.fetchall():
#                 party_data = {
#                     "id": row[0],
#                     "name": row[1] if len(row) > 1 and row[1] is not None else str(row[0])
#                 }
                
#                 # Add address if available
#                 if len(row) > 2 and row[2] is not None:
#                     party_data["address"] = str(row[2]).strip()
                
#                 # Add pincode if available
#                 if len(row) > 3 and row[3] is not None:
#                     pincode_val = str(row[3]).strip()
#                     # Try to extract 6-digit pincode
#                     pincode_match = re.search(r'(\d{6})', pincode_val)
#                     if pincode_match:
#                         party_data["pincode"] = pincode_match.group(1)
#                     elif re.match(r'^\d{6}$', pincode_val):
#                         party_data["pincode"] = pincode_val
                
#                 # Add GST if available
#                 if len(row) > 4 and row[4] is not None:
#                     party_data["gst"] = str(row[4]).strip()
                
#                 # If pincode is missing but address has a pincode, extract it
#                 if "pincode" not in party_data and "address" in party_data:
#                     address = party_data["address"]
#                     # Look for 6-digit number in the address (usually at the end)
#                     pincode_match = re.search(r'(\d{6})', address)
#                     if pincode_match:
#                         party_data["pincode"] = pincode_match.group(1)
                
#                 parties.append(party_data)
            
#             return parties
#     except Exception as e:
#         print(f"Error in get_parties: {e}")
#         return []

# def get_invoice_types():
#     """Get invoice types from database with mappings"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("SHOW COLUMNS FROM invoices LIKE 'type'")
#             result = conn.execute(query)
#             if result.fetchone():
#                 query = text("SELECT DISTINCT type FROM invoices WHERE type IS NOT NULL AND type != '' ORDER BY type")
#                 result = conn.execute(query)
#                 types = [row[0] for row in result.fetchall()]
#                 if types:
#                     # Add codes to existing types based on your database values
#                     type_with_codes = []
#                     for t in types:
#                         code = get_type_code(t)
#                         type_with_codes.append(f"{t} ({code})")
#                     return type_with_codes
        
#         # Fallback to default types with codes
#         return [
#             "sales (INV)",
#             "purchase (PI)", 
#             "purchase_order (PO)",
#             "credit (CN)",
#             "debit (DN)",
#             "delivery_challan (DCH)"
#         ]
#     except Exception as e:
#         # Return your database types as default
#         return [
#             "sales (INV)",
#             "purchase (PI)", 
#             "purchase_order (PO)",
#             "credit (CN)",
#             "debit (DN)",
#             "delivery_challan (DCH)"
#         ]

# def get_type_code(invoice_type):
#     """Get code for invoice type"""
#     # Clean the invoice type - remove any parentheses and trim
#     clean_type = invoice_type.strip().lower()
    
#     # First, handle the exact types from your database
#     if clean_type == "purchase":
#         return "PI"
#     elif clean_type == "purchase_order":
#         return "PO"
#     elif clean_type == "sales":
#         return "INV"
#     elif clean_type == "credit":
#         return "CN"
#     elif clean_type == "debit":
#         return "DN"
#     elif clean_type == "delivery_challan":
#         return "DCH"
    
#     # Then handle other variations
#     type_mapping = {
#         "credit": "CN",
#         "debit": "DN", 
#         "delivery challan": "DCH",
#         "delivery_challan": "DCH",
#         "purchase": "PI",
#         "purchase invoice": "PI",
#         "purchase order": "PO",
#         "purchase_order": "PO",
#         "sales": "INV",
#         "sales invoice": "INV",
#         "tax invoice": "INV",
#         "proforma invoice": "PINV",
#         "credit note": "CN",
#         "debit note": "DN", 
#         "delivery challan (dch)": "DCH",
#         "purchase invoice (pi)": "PI",
#         "purchase order (po)": "PO",
#         "sales invoice (inv)": "INV",
#         "tax invoice (inv)": "INV",
#         "proforma invoice (pınv)": "PINV"
#     }
    
#     # Try exact match first
#     if clean_type in type_mapping:
#         return type_mapping[clean_type]
    
#     # Try partial match
#     for key in type_mapping:
#         if key in clean_type or clean_type in key:
#             return type_mapping[key]
    
#     # Default
#     return "INV"

# def get_product_id(product_name):
#     """Get product ID from boq_items table"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("SELECT id FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
#             result = conn.execute(query, {"p": product_name})
#             row = result.fetchone()
#             if row:
#                 return row[0]
#             return None
#     except Exception as e:
#         print(f"Error getting product ID for {product_name}: {e}")
#         return None

# def get_product_options():
#     """Fetch all products from database"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("SELECT DISTINCT item_description FROM boq_items ORDER BY item_description")
#             result = conn.execute(query)
#             products = [row[0] for row in result.fetchall()]
#             return products
#     except Exception as e:
#         return []

# def get_product_stock(product_name):
#     """Get available stock quantity for a product from boq_items table"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("""
#                 SELECT quantity 
#                 FROM boq_items 
#                 WHERE LOWER(item_description) = LOWER(:p)
#             """)
#             result = conn.execute(query, {"p": product_name})
#             row = result.fetchone()
#             if row:
#                 return float(row[0])
#             return None
#     except Exception as e:
#         print(f"Error getting stock for {product_name}: {e}")
#         return None

# def check_product_exists(product_name):
#     """Check if product exists in database and return id, price, stock"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("SELECT id, supply_rate, quantity FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
#             result = conn.execute(query, {"p": product_name})
#             row = result.fetchone()
#             if row:
#                 # Convert to appropriate types
#                 product_id = int(row[0]) if row[0] is not None else None
#                 price = float(row[1]) if row[1] is not None else None
#                 stock = float(row[2]) if row[2] is not None else None
#                 return True, product_id, price, stock
#             return False, None, None, None
#     except Exception as e:
#         print(f"Error checking product: {e}")
#         return False, None, None, None

# def check_product_exists_simple(product_name):
#     """Simple version - returns (exists, price, stock) for backward compatibility"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("SELECT supply_rate, quantity FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
#             result = conn.execute(query, {"p": product_name})
#             row = result.fetchone()
#             if row:
#                 price = float(row[0]) if row[0] is not None else None
#                 stock = float(row[1]) if row[1] is not None else None
#                 return True, price, stock
#             return False, None, None
#     except Exception as e:
#         print(f"Error checking product (simple): {e}")
#         return False, None, None

# def add_product_to_db(product_name, price, initial_stock=0):
#     """Add new product to database"""
#     try:
#         with ENGINE.begin() as conn:
#             query = text("""
#                 INSERT INTO boq_items 
#                 (project_id, item_description, quantity, unit, supply_rate, created_by)
#                 VALUES (1, :p, :qty, 'nos', :r, 1)
#             """)
#             conn.execute(query, {"p": product_name, "r": price, "qty": initial_stock})
#         return True, "Product added successfully"
#     except Exception as e:
#         return False, f"Error adding product: {str(e)}"

# def update_product_price(product_name, new_price):
#     """Update product price in database"""
#     try:
#         with ENGINE.begin() as conn:
#             query = text("""
#                 UPDATE boq_items 
#                 SET supply_rate = :r 
#                 WHERE LOWER(item_description) = LOWER(:p)
#             """)
#             conn.execute(query, {"p": product_name, "r": new_price})
#         return True, "Price updated successfully"
#     except Exception as e:
#         return False, f"Error updating price: {str(e)}"

# def remove_product_from_invoice(product_name):
#     """Remove product from current invoice"""
#     product_lower = product_name.lower()
#     removed = False
#     original_length = len(st.session_state.invoice)
    
#     # Filter out the product to be removed
#     new_invoice = []
#     for item in st.session_state.invoice:
#         if item["item_description"].lower() != product_lower:
#             new_invoice.append(item)
#         else:
#             removed = True
    
#     # Update the invoice
#     st.session_state.invoice = new_invoice
    
#     if removed:
#         return True, f"✅ Removed '{product_name}' from invoice"
#     else:
#         return False, f"❌ '{product_name}' not found in current invoice"

# def update_product_stock(product_name, new_stock):
#     """Update product stock quantity in database"""
#     try:
#         with ENGINE.begin() as conn:
#             query = text("""
#                 UPDATE boq_items 
#                 SET quantity = :qty 
#                 WHERE LOWER(item_description) = LOWER(:p)
#             """)
#             conn.execute(query, {"p": product_name, "qty": new_stock})
#         return True, "Stock updated successfully"
#     except Exception as e:
#         return False, f"Error updating stock: {str(e)}"

# def increase_product_stock(product_name, additional_stock):
#     """Increase product stock quantity"""
#     try:
#         current_stock = get_product_stock(product_name)
#         if current_stock is None:
#             return False, "Product not found"
        
#         new_stock = current_stock + additional_stock
#         success, message = update_product_stock(product_name, new_stock)
#         if success:
#             return True, f"✅ Stock increased by {additional_stock}. New stock: {new_stock}"
#         return False, message
#     except Exception as e:
#         return False, f"Error increasing stock: {str(e)}"

# def decrease_product_stock(product_name, quantity_to_decrease):
#     """Decrease product stock quantity after invoice generation"""
#     try:
#         current_stock = get_product_stock(product_name)
#         if current_stock is None:
#             return False, "Product not found"
        
#         if current_stock < quantity_to_decrease:
#             return False, f"Insufficient stock. Available: {current_stock}, Required: {quantity_to_decrease}"
        
#         new_stock = current_stock - quantity_to_decrease
#         success, message = update_product_stock(product_name, new_stock)
#         if success:
#             return True, f"✅ Stock decreased by {quantity_to_decrease}. Remaining stock: {new_stock}"
#         return False, message
#     except Exception as e:
#         return False, f"Error decreasing stock: {str(e)}"

# def get_next_invoice_number():
#     """Get next invoice number using format: ICE/2025-2026/[TYPE]/[SEQUENCE]"""
#     try:
#         with ENGINE.connect() as conn:
#             # Get invoice type from session state
#             invoice_type = st.session_state.invoice_meta.get("invoice_type", "sales")
            
#             # Get type code using the mapping function
#             type_code = get_type_code(invoice_type)
            
#             # Get current financial year (assuming Apr-Mar) - use 4-digit year
#             current_year = datetime.now().year
#             if datetime.now().month >= 4:
#                 fin_year = f"{current_year}-{current_year+1}"
#             else:
#                 fin_year = f"{current_year-1}-{current_year}"
            
#             print(f"Generating invoice number for type: '{invoice_type}' -> code: '{type_code}'")
            
#             # First, try to get sequence from invoice_settings table
#             query = text("SHOW TABLES LIKE 'invoice_settings'")
#             result = conn.execute(query)
            
#             if result.fetchone():
#                 # Get the current sequence for this type
#                 query = text("""
#                     SELECT invoice_prefix, invoice_sequence, invoice_type_code 
#                     FROM invoice_settings 
#                     WHERE invoice_type_code = :type_code
#                     LIMIT 1
#                 """)
#                 result = conn.execute(query, {"type_code": type_code})
#                 row = result.fetchone()
                
#                 if row:
#                     prefix = row[0] or "ICE"
#                     sequence = row[1] or 1
                    
#                     # Update sequence for next invoice
#                     update_query = text("""
#                         UPDATE invoice_settings 
#                         SET invoice_sequence = :seq + 1 
#                         WHERE invoice_type_code = :type_code
#                     """)
#                     conn.execute(update_query, {"seq": sequence, "type_code": type_code})
#                     conn.commit()
                    
#                     invoice_number = f"{prefix}/{fin_year}/{type_code}/{str(sequence).zfill(4)}"
#                     print(f"Generated from invoice_settings: {invoice_number}")
#                     return invoice_number, prefix, sequence, type_code
                
#                 # If no record for this type, create one
#                 else:
#                     # Start sequence from 1 for new type
#                     sequence = 1
                    
#                     # Insert new record for this type
#                     insert_query = text("""
#                         INSERT INTO invoice_settings 
#                         (invoice_prefix, invoice_sequence, invoice_type_code, created_at)
#                         VALUES (:prefix, :seq, :type_code, NOW())
#                     """)
#                     conn.execute(insert_query, {
#                         "prefix": "ICE",
#                         "seq": sequence,
#                         "type_code": type_code
#                     })
#                     conn.commit()
                    
#                     invoice_number = f"ICE/{fin_year}/{type_code}/{str(sequence).zfill(4)}"
#                     print(f"Created new record in invoice_settings: {invoice_number}")
#                     return invoice_number, "ICE", sequence, type_code
            
#             # Fallback: Check invoices table for last sequence of this type
#             else:
#                 # Try different patterns
#                 patterns = [
#                     f"%ICE/{fin_year}/{type_code}/%",
#                     f"%{fin_year}/{type_code}/%",
#                     f"%/{type_code}/%"
#                 ]
                
#                 last_sequence = 0
#                 for pattern in patterns:
#                     query = text("""
#                         SELECT invoiceNumber, invoice_number_generated 
#                         FROM invoices 
#                         WHERE invoiceNumber LIKE :pattern OR invoice_number_generated LIKE :pattern
#                         ORDER BY createdAt DESC 
#                         LIMIT 1
#                     """)
#                     result = conn.execute(query, {"pattern": pattern})
#                     row = result.fetchone()
                    
#                     if row:
#                         # Extract the last sequence number
#                         invoice_str = row[0] or row[1] or ""
#                         match = re.search(r'/(\d{4})$', invoice_str)
#                         if match:
#                             last_seq = int(match.group(1))
#                             last_sequence = max(last_sequence, last_seq)
                
#                 sequence = last_sequence + 1 if last_sequence > 0 else 1
#                 invoice_number = f"ICE/{fin_year}/{type_code}/{str(sequence).zfill(4)}"
#                 print(f"Generated from invoices table: {invoice_number}")
#                 return invoice_number, "ICE", sequence, type_code
                
#     except Exception as e:
#         print(f"Error in get_next_invoice_number: {e}")
#         # Fallback format
#         current_year = datetime.now().year
#         if datetime.now().month >= 4:
#             fin_year = f"{current_year}-{current_year+1}"
#         else:
#             fin_year = f"{current_year-1}-{current_year}"
        
#         # Get type code
#         invoice_type = st.session_state.invoice_meta.get("invoice_type", "sales")
#         type_code = get_type_code(invoice_type)
        
#         fallback_number = f"ICE/{fin_year}/{type_code}/0001"
#         print(f"Using fallback: {fallback_number}")
#         return fallback_number, "ICE", 1, type_code
        
#         # # In the chat engine function, add this debug command
#         # if text == "debug type mapping":
#         #     invoice_type = st.session_state.invoice_meta.get("invoice_type")
#         #     type_code = get_type_code(invoice_type)
            
#         #     response = f"🔍 **Type Mapping Debug:**\n\n"
#         #     response += f"**Current invoice_type in session:** '{invoice_type}'\n"
#         #     response += f"**Mapped type_code:** '{type_code}'\n\n"
#         #     response += "**Available mappings:**\n"
#         #     response += "• 'Purchase Order' → 'PO'\n"
#         #     response += "• 'Sales Invoice' → 'INV'\n"
#         #     response += "• 'Purchase Invoice' → 'PI'\n"
#         #     response += "• 'Credit Note' → 'CN'\n"
#         #     response += "• 'Debit Note' → 'DN'\n"
#         #     response += "• 'Delivery Challan' → 'DCH'\n"
#         #     response += "• 'Proforma Invoice' → 'PINV'\n"
            
#         #     return response
        
#         # return f"ICE/{fin_year}/{type_code}/0001", "ICE", 1, type_code

# def debug_database_tables():
#     """Debug all database tables"""
#     try:
#         with ENGINE.connect() as conn:
#             # Get all tables
#             query = text("SHOW TABLES")
#             result = conn.execute(query)
#             tables = [row[0] for row in result.fetchall()]
            
#             return tables
#     except Exception as e:
#         return f"Error: {e}"
    

# def debug_all_invoice_numbers():
#     """Debug function to see all invoice numbers in database"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("""
#                 SELECT 
#                     id,
#                     invoiceNumber,
#                     invoice_number_generated,
#                     type,
#                     date,
#                     total,
#                     status,
#                     createdAt
#                 FROM invoices 
#                 ORDER BY createdAt DESC
#                 LIMIT 20
#             """)
#             result = conn.execute(query)
            
#             invoices = []
#             for row in result.fetchall():
#                 invoices.append({
#                     "id": row[0],
#                     "invoiceNumber": row[1],
#                     "invoice_number_generated": row[2],
#                     "type": row[3],
#                     "date": row[4],
#                     "total": row[5],
#                     "status": row[6],
#                     "createdAt": row[7]
#                 })
            
#             return invoices
#     except Exception as e:
#         return f"Error: {e}"    

# def debug_table_structure(table_name):
#     """Debug table structure"""
#     try:
#         with ENGINE.connect() as conn:
#             # Get all columns
#             query = text(f"SHOW COLUMNS FROM {table_name}")
#             result = conn.execute(query)
#             columns = []
#             for row in result.fetchall():
#                 columns.append({
#                     "field": row[0],
#                     "type": row[1],
#                     "null": row[2],
#                     "key": row[3],
#                     "default": row[4],
#                     "extra": row[5]
#                 })
            
#             # Get sample data
#             query = text(f"SELECT * FROM {table_name} LIMIT 3")
#             result = conn.execute(query)
#             sample_data = result.fetchall()
            
#             return {
#                 "columns": columns,
#                 "sample_data": sample_data
#             }
#     except Exception as e:
#         return f"Error: {e}"

# def debug_search_invoices(search_term=""):
#     """Debug: Search for invoices in database"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("""
#                 SELECT 
#                     invoice_number_generated, 
#                     invoiceNumber,
#                     UPPER(invoice_number_generated) as upper_gen,
#                     UPPER(invoiceNumber) as upper_num,
#                     date, type, total, project_id, clientId
#                 FROM invoices 
#                 WHERE invoice_number_generated IS NOT NULL OR invoiceNumber IS NOT NULL
#                 ORDER BY createdAt DESC 
#                 LIMIT 20
#             """)
#             result = conn.execute(query)
            
#             invoices = []
#             for row in result.fetchall():
#                 invoices.append({
#                     "invoice_number_generated": row[0],
#                     "invoiceNumber": row[1],
#                     "upper_generated": row[2],
#                     "upper_number": row[3],
#                     "date": row[4],
#                     "type": row[5],
#                     "total": row[6],
#                     "project_id": row[7],
#                     "clientId": row[8]
#                 })
            
#             return invoices
#     except Exception as e:
#         return f"Error: {e}"

# def debug_invoice_items_table():
#     """Debug the invoice_items table structure"""
#     try:
#         with ENGINE.connect() as conn:
#             # Check if table exists
#             query = text("SHOW TABLES LIKE 'invoice_items'")
#             result = conn.execute(query)
#             if not result.fetchone():
#                 return "❌ invoice_items table does not exist"
            
#             # Get table structure
#             query = text("SHOW COLUMNS FROM invoice_items")
#             result = conn.execute(query)
#             columns = []
#             for row in result.fetchall():
#                 columns.append({
#                     "field": row[0],
#                     "type": row[1],
#                     "null": row[2],
#                     "key": row[3],
#                     "default": row[4],
#                     "extra": row[5]
#                 })
            
#             # Get sample data
#             query = text("SELECT * FROM invoice_items LIMIT 3")
#             result = conn.execute(query)
#             sample_data = result.fetchall()
            
#             return {
#                 "columns": columns,
#                 "sample_data": sample_data
#             }
#     except Exception as e:
#         return f"Error: {e}"

#     # Add this debug command to the chat engine
#     # In the chat engine function, add:
#     if text == "debug invoice items":
#         debug_info = debug_invoice_items_table()
#         if isinstance(debug_info, str):
#             return debug_info
        
#         response = "🔍 **invoice_items Table Structure:**\n\n"
#         response += "**Columns:**\n"
#         for col in debug_info["columns"]:
#             response += f"• {col['field']} ({col['type']}) - Null: {col['null']}\n"
        
#         response += "\n**Sample Data (first 3 rows):**\n"
#         for i, row in enumerate(debug_info["sample_data"], 1):
#             response += f"{i}. {row}\n"
        
#         return response

# def get_invoice_by_number(invoice_no):
#     """Get invoice details by invoice number - searches in invoiceNumber column"""
#     try:
#         with ENGINE.connect() as conn:
#             # Clean the input
#             clean_invoice_no = str(invoice_no).strip()
            
#             print(f"Searching for invoice: '{clean_invoice_no}'")  # Debug
            
#             # Strategy 1: Search in invoiceNumber column (exact match)
#             query = text("""
#                 SELECT 
#                     invoiceNumber, project_id, clientId, type, date,
#                     subTotal, tax, discount, total, 
#                     notes, meta, invoice_prefix, invoice_sequence,
#                     status, createdAt, updatedAt
#                 FROM invoices 
#                 WHERE invoiceNumber = :no
#                 ORDER BY createdAt DESC
#                 LIMIT 1
#             """)
#             result = conn.execute(query, {"no": clean_invoice_no})
#             header = result.fetchone()
            
#             # Strategy 2: Try in invoice_number_generated column
#             if not header:
#                 query = text("""
#                     SELECT 
#                         invoice_number_generated, project_id, clientId, type, date,
#                         subTotal, tax, discount, total, 
#                         notes, meta, invoice_prefix, invoice_sequence,
#                         status, createdAt, updatedAt, invoice_type_code
#                     FROM invoices 
#                     WHERE invoice_number_generated = :no
#                     ORDER BY createdAt DESC
#                     LIMIT 1
#                 """)
#                 result = conn.execute(query, {"no": clean_invoice_no})
#                 header = result.fetchone()
                
#                 if header:
#                     # Convert to match expected structure
#                     header = list(header)
#                     header[0] = header[0]  # Keep invoice_number_generated as invoiceNumber
            
#             # Strategy 3: Case-insensitive search in invoiceNumber
#             if not header:
#                 query = text("""
#                     SELECT 
#                         invoiceNumber, project_id, clientId, type, date,
#                         subTotal, tax, discount, total, 
#                         notes, meta, invoice_prefix, invoice_sequence,
#                         status, createdAt, updatedAt, invoice_type_code
#                     FROM invoices 
#                     WHERE UPPER(invoiceNumber) = UPPER(:no)
#                     ORDER BY createdAt DESC
#                     LIMIT 1
#                 """)
#                 result = conn.execute(query, {"no": clean_invoice_no})
#                 header = result.fetchone()
            
#             # Strategy 4: Try without any special formatting
#             if not header:
#                 # Remove all spaces and try
#                 clean_no_no_spaces = clean_invoice_no.replace(" ", "")
#                 query = text("""
#                     SELECT 
#                         invoiceNumber, project_id, clientId, type, date,
#                         subTotal, tax, discount, total, 
#                         notes, meta, invoice_prefix, invoice_sequence,
#                         status, createdAt, updatedAt, invoice_type_code
#                     FROM invoices 
#                     WHERE REPLACE(invoiceNumber, ' ', '') = :no
#                     ORDER BY createdAt DESC
#                     LIMIT 1
#                 """)
#                 result = conn.execute(query, {"no": clean_no_no_spaces})
#                 header = result.fetchone()
            
#             # Strategy 5: Partial match search
#             if not header:
#                 # Try with different patterns
#                 patterns = [
#                     f"%{clean_invoice_no}%",
#                     f"%{clean_invoice_no.replace('/', '/')}%",
#                     f"%{clean_invoice_no.replace('ICE/', '')}%",
#                     f"%INV/{clean_invoice_no.split('/')[-1] if '/' in clean_invoice_no else clean_invoice_no}%"
#                 ]
                
#                 for pattern in patterns:
#                     query = text("""
#                         SELECT 
#                             invoiceNumber, project_id, clientId, type, date,
#                             subTotal, tax, discount, total, 
#                             notes, meta, invoice_prefix, invoice_sequence,
#                             status, createdAt, updatedAt, invoice_type_code
#                         FROM invoices 
#                         WHERE invoiceNumber LIKE :pattern
#                         ORDER BY createdAt DESC
#                         LIMIT 1
#                     """)
#                     result = conn.execute(query, {"pattern": pattern})
#                     header = result.fetchone()
#                     if header:
#                         break
            
#             # Strategy 6: Search by sequence number only
#             if not header:
#                 # Extract just the numeric part (last 4 digits)
#                 match = re.search(r'(\d{4})$', clean_invoice_no)
#                 if match:
#                     seq_num = match.group(1)
#                     query = text("""
#                         SELECT 
#                             invoiceNumber, project_id, clientId, type, date,
#                             subTotal, tax, discount, total, 
#                             notes, meta, invoice_prefix, invoice_sequence,
#                             status, createdAt, updatedAt, invoice_type_code
#                         FROM invoices 
#                         WHERE invoiceNumber LIKE :pattern
#                         ORDER BY createdAt DESC
#                         LIMIT 1
#                     """)
#                     result = conn.execute(query, {"pattern": f"%/{seq_num}"})
#                     header = result.fetchone()
            
#             if header:
#                 invoice_number = header[0]
#                 print(f"Found invoice: {invoice_number}")
                
#                 # Get project name
#                 project_name = "Unknown"
#                 try:
#                     query = text("SELECT project_name FROM projects WHERE id = :id")
#                     result = conn.execute(query, {"id": header[1]})
#                     project_row = result.fetchone()
#                     if project_row:
#                         project_name = project_row[0]
#                 except Exception as e:
#                     print(f"Error getting project name: {e}")
                
#                 # Get party/client name
#                 party_name = "Unknown"
#                 party_address = None
#                 party_pincode = None
#                 party_gst = None
                
#                 try:
#                     # First check what columns exist in parties table
#                     query = text("SHOW COLUMNS FROM parties")
#                     result = conn.execute(query)
#                     columns = [row[0] for row in result.fetchall()]
                    
#                     # Determine the name column
#                     name_column = None
#                     possible_name_columns = ['party_name', 'name', 'company_name', 'customer_name', 'vendor_name', 'client_name']
                    
#                     for col in possible_name_columns:
#                         if col in columns:
#                             name_column = col
#                             break
                    
#                     if not name_column and columns:
#                         for col in columns:
#                             if col not in ['id', 'createdAt', 'updatedAt', 'status']:
#                                 name_column = col
#                                 break
                    
#                     # Build query to get party info
#                     if name_column:
#                         select_parts = [f"{name_column} as party_name"]
                        
#                         # Check for address column
#                         address_columns = ['address', 'billingAddress', 'billing_address', 'party_address', 'street', 'city']
#                         for col in address_columns:
#                             if col in columns:
#                                 select_parts.append(f"{col} as address")
#                                 break
                        
#                         # Check for pincode column
#                         pincode_columns = ['pincode', 'pin_code', 'postal_code', 'zip_code']
#                         for col in pincode_columns:
#                             if col in columns:
#                                 select_parts.append(f"{col} as pincode")
#                                 break
                        
#                         # Check for GST column
#                         gst_columns = ['gst_number', 'gst', 'gstin', 'gst_no']
#                         for col in gst_columns:
#                             if col in columns:
#                                 select_parts.append(f"{col} as gst")
#                                 break
                        
#                         query_str = f"SELECT {', '.join(select_parts)} FROM parties WHERE id = :id"
#                         query = text(query_str)
#                         result = conn.execute(query, {"id": header[2]})
#                         party_row = result.fetchone()
                        
#                         if party_row:
#                             party_name = party_row[0] if party_row[0] else "Unknown"
#                             if len(party_row) > 1:
#                                 party_address = party_row[1]
#                             if len(party_row) > 2:
#                                 party_pincode = party_row[2]
#                             if len(party_row) > 3:
#                                 party_gst = party_row[3]
#                 except Exception as e:
#                     print(f"Error getting party info: {e}")
                
#                 # Try to get invoice items
#                 items = []
                
#                 # First try from invoice_items table
#                 try:
#                     query = text("SHOW TABLES LIKE 'invoice_items'")
#                     result = conn.execute(query)
#                     if result.fetchone():
#                         query = text("""
#                             SELECT 
#                                 item_description, quantity, unit_price, total_price
#                             FROM invoice_items 
#                             WHERE invoice_no = :no
#                         """)
#                         result = conn.execute(query, {"no": invoice_number})
#                         db_items = result.fetchall()
#                         if db_items:
#                             items = db_items
#                 except Exception as e:
#                     print(f"Error getting invoice items: {e}")
                
#                 # If no items found, try from notes JSON
#                 if not items and header[9]:  # notes column
#                     try:
#                         notes_data = json.loads(header[9])
#                         if isinstance(notes_data, dict):
#                             # Check different possible structures
#                             if 'items' in notes_data:
#                                 for item in notes_data['items']:
#                                     items.append((
#                                         item.get('description', '') or item.get('item_description', ''),
#                                         item.get('quantity', 0),
#                                         item.get('unit_price', 0) or item.get('rate', 0) or item.get('price', 0),
#                                         item.get('total', 0) or item.get('amount', 0)
#                                     ))
#                             elif 'line_items' in notes_data:
#                                 for item in notes_data['line_items']:
#                                     items.append((
#                                         item.get('description', '') or item.get('item_description', ''),
#                                         item.get('quantity', 0),
#                                         item.get('unit_price', 0) or item.get('rate', 0) or item.get('price', 0),
#                                         item.get('total', 0) or item.get('amount', 0)
#                                     ))
#                     except Exception as e:
#                         print(f"Error parsing notes JSON: {e}")
                
#                 # Format invoice data
#                 invoice_data = {
#                     "header": {
#                         "invoice_no": invoice_number,
#                         "project_id": header[1],
#                         "project_name": project_name,
#                         "party_id": header[2],
#                         "party_name": party_name,
#                         "invoice_type": header[3],
#                         "invoice_date": header[4],
#                         "subtotal": float(header[5]) if header[5] else 0,
#                         "tax": float(header[6]) if header[6] else 0,
#                         "discount": float(header[7]) if header[7] else 0,
#                         "grand_total": float(header[8]) if header[8] else 0,
#                         "notes": header[9],
#                         "meta": header[10],
#                         "invoice_prefix": header[11],
#                         "invoice_sequence": header[12],
#                         "status": header[13],
#                         "created_at": header[14],
#                         "updated_at": header[15],
#                         "invoice_type_code": header[16] if len(header) > 16 else None,
#                         "party_address": party_address,
#                         "party_pincode": party_pincode,
#                         "party_gst": party_gst
#                     },
#                     "items": []
#                 }
                
#                 for item in items:
#                     invoice_data["items"].append({
#                         "item_description": item[0],
#                         "quantity": float(item[1]) if item[1] else 0,
#                         "unit_price": float(item[2]) if item[2] else 0,
#                         "total_price": float(item[3]) if item[3] else 0
#                     })
                
#                 return invoice_data
            
#             return None
#     except Exception as e:
#         print(f"Error in get_invoice_by_number: {e}")
#         return None

# def get_all_invoices():
#     """Get list of all invoices from database"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("""
#                 SELECT 
#                     invoiceNumber,
#                     date, project_id, clientId, type, total, status
#                 FROM invoices 
#                 WHERE invoiceNumber IS NOT NULL AND invoiceNumber != ''
#                 ORDER BY createdAt DESC 
#                 LIMIT 50
#             """)
#             result = conn.execute(query)
#             invoices = []
#             for row in result.fetchall():
#                 invoices.append({
#                     "invoice_no": str(row[0]).strip(),
#                     "invoice_date": row[1],
#                     "project_id": row[2],
#                     "party_id": row[3],
#                     "invoice_type": row[4],
#                     "grand_total": float(row[5]) if row[5] else 0,
#                     "status": row[6]
#                 })
#             return invoices
#     except Exception as e:
#         print(f"Error in get_all_invoices: {e}")
#         return []
    
# def save_invoice_to_db():
#     """Save invoice to database with all information including GST and update stock"""
#     try:
#         if not st.session_state.invoice:
#             return False, "No items in invoice"
        
#         if not st.session_state.invoice_meta["project_id"]:
#             return False, "Project not selected"
        
#         if not st.session_state.invoice_meta["party_id"]:
#             return False, "Party not selected"
        
#         if not st.session_state.invoice_meta["invoice_type"]:
#             return False, "Invoice type not selected"
        
#         # Validate and calculate subtotal with error handling
#         subtotal = 0
#         valid_items = []
        
#         for item in st.session_state.invoice:
#             # Check if values exist and are valid
#             qty = item.get("qty")
#             price = item.get("supply_rate")
            
#             # Skip invalid items
#             if qty is None or price is None:
#                 continue
                
#             # Convert to float if needed
#             try:
#                 qty = float(qty)
#                 price = float(price)
                
#                 # Ensure positive values
#                 if qty <= 0 or price <= 0:
#                     continue
                    
#                 subtotal += qty * price
#                 valid_items.append(item)
                
#             except (ValueError, TypeError):
#                 continue
        
#         if not valid_items:
#             return False, "No valid items with quantity and price in invoice"
        
#         # Update invoice with only valid items
#         st.session_state.invoice = valid_items
        
#         pincode = st.session_state.invoice_meta["party_pincode"]
#         gst_calc = calculate_gst_breakdown(subtotal, pincode)
        
#         # Get invoice number with new format
#         invoice_no, prefix, sequence, type_code = get_next_invoice_number()
        
#         # Store the invoice number in session for display
#         st.session_state.invoice_meta["invoice_no"] = invoice_no
#         st.session_state.invoice_meta["invoice_prefix"] = prefix
#         st.session_state.invoice_meta["invoice_sequence"] = sequence
#         st.session_state.invoice_meta["invoice_type_code"] = type_code
        
#         with ENGINE.begin() as conn:
#             # First check what columns exist in invoices table
#             query = text("SHOW COLUMNS FROM invoices")
#             result = conn.execute(query)
#             invoice_columns = [row[0] for row in result.fetchall()]
            
#             # Insert invoice header
#             # Check if invoice_number_generated column exists
#             if 'invoice_number_generated' in invoice_columns:
#                 # Use invoice_number_generated column
#                 query = text("""
#                     INSERT INTO invoices 
#                     (project_id, clientId, type, invoice_number_generated, invoiceNumber, date,
#                      subTotal, tax, total, status, createdAt)
#                     VALUES (:p, :pt, :t, :no, :inv_no, CURDATE(), 
#                             :sub, :tax, :total, 'draft', NOW())
#                 """)
#             else:
#                 # Only use invoiceNumber column
#                 query = text("""
#                     INSERT INTO invoices 
#                     (project_id, clientId, type, invoiceNumber, date,
#                      subTotal, tax, total, status, createdAt)
#                     VALUES (:p, :pt, :t, :inv_no, CURDATE(), 
#                             :sub, :tax, :total, 'draft', NOW())
#                 """)
            
#             params = {
#                 "p": st.session_state.invoice_meta["project_id"],
#                 "pt": st.session_state.invoice_meta["party_id"],
#                 "t": st.session_state.invoice_meta["invoice_type"],
#                 "inv_no": invoice_no,
#                 "sub": subtotal,
#                 "tax": gst_calc["total_gst"],
#                 "total": gst_calc["grand_total"]
#             }
            
#             if 'invoice_number_generated' in invoice_columns:
#                 params["no"] = invoice_no
            
#             conn.execute(query, params)
            
#             # Get the auto-generated invoice ID
#             query = text("SELECT LAST_INSERT_ID()")
#             result = conn.execute(query)
#             invoice_id = result.fetchone()[0]
            
#             # Update stock for each item
#             stock_updates = []
#             for item in st.session_state.invoice:
#                 product_name = item["item_description"]
#                 qty = float(item["qty"])
                
#                 # Get current stock
#                 current_stock = get_product_stock(product_name)
#                 if current_stock is not None:
#                     current_stock = float(current_stock)
#                     if current_stock >= qty:
#                         # Decrease stock
#                         new_stock = current_stock - qty
#                         update_query = text("""
#                             UPDATE boq_items 
#                             SET quantity = :new_qty 
#                             WHERE LOWER(item_description) = LOWER(:p)
#                         """)
#                         conn.execute(update_query, {"p": product_name, "new_qty": new_stock})
#                         stock_updates.append(f"✅ {product_name}: {current_stock} → {new_stock} (reduced by {qty})")
#                     else:
#                         stock_updates.append(f"⚠️ {product_name}: Insufficient stock! Available: {current_stock}, Required: {qty}")
            
#             # Insert invoice items
#             for item in st.session_state.invoice:
#                 # Calculate total amount for this item
#                 item_total = float(item["qty"]) * float(item["supply_rate"])
                
#                 # Get product ID from boq_items table
#                 product_id = get_product_id(item["item_description"])
                
#                 # Insert into invoice_items table with itemId
#                 item_query = text("""
#                     INSERT INTO invoice_items 
#                     (invoiceId, itemId, description, quantity, rate, amount)
#                     VALUES (:inv_id, :item_id, :desc, :qty, :rate, :amount)
#                 """)
                
#                 item_params = {
#                     "inv_id": invoice_id,
#                     "item_id": product_id if product_id else None,  # Use None if product not found
#                     "desc": item["item_description"],
#                     "qty": float(item["qty"]),
#                     "rate": float(item["supply_rate"]),
#                     "amount": item_total
#                 }
                
#                 conn.execute(item_query, item_params)
        
#         # Update meta
#         st.session_state.invoice_meta.update({
#             "invoice_no": invoice_no,
#             "invoice_prefix": prefix,
#             "invoice_sequence": sequence,
#             "invoice_type_code": type_code,
#             "total_amount": subtotal,
#             "cgst": gst_calc["cgst_amount"],
#             "sgst": gst_calc["sgst_amount"],
#             "igst": gst_calc["igst_amount"],
#             "grand_total": gst_calc["grand_total"],
#             "invoice_date": datetime.now().strftime("%Y-%m-%d")
#         })
        
#         # Prepare response with stock updates
#         response = f"✅ **Invoice #{invoice_no} generated successfully!**\n\n"
#         response += f"📋 **Invoice Details:**\n"
#         response += f"• **Invoice Number:** `{invoice_no}`\n"
#         response += f"• **Project:** {st.session_state.invoice_meta['project_name']}\n"
#         response += f"• **Party:** {st.session_state.invoice_meta['party_name']}\n"
#         response += f"• **Type:** {st.session_state.invoice_meta['invoice_type']} ({type_code})\n"
#         response += f"• **Address:** {st.session_state.invoice_meta['party_address'] or 'N/A'}\n"
#         response += f"• **Pincode:** {st.session_state.invoice_meta['party_pincode'] or 'N/A'}\n"
#         response += f"• **GST:** {st.session_state.invoice_meta['party_gst'] or 'N/A'}\n"
#         response += f"• **Subtotal:** ₹{subtotal:,.2f}\n"
#         response += f"• **GST ({gst_calc['gst_type']}):** ₹{gst_calc['total_gst']:,.2f}\n"
#         response += f"• **Grand Total:** ₹{gst_calc['grand_total']:,.2f}\n"
#         response += f"• **Items:** {len(st.session_state.invoice)}\n"
#         response += f"• **Sequence:** {sequence}\n"
#         response += f"• **Invoice ID:** {invoice_id}\n\n"
        
#         if stock_updates:
#             response += "**Stock Updates:**\n"
#             for update in stock_updates:
#                 response += f"• {update}\n"
        
#         # Clear invoice after generation
#         st.session_state.invoice = []
#         st.session_state.stock_alert = []
        
#         return True, response
#     except Exception as e:
#         print(f"Error in save_invoice_to_db: {e}")
#         return False, f"Error saving invoice: {str(e)}"

# # =========================
# # NLP FUNCTIONS
# # =========================

# def extract_product_qty_price(text):
#     """Extract product, quantity and price from text"""
#     text_lower = text.lower().strip()
    
#     product = None
#     qty = None
#     price = None
    
#     # Check for "more" pattern first
#     more_match = re.search(r'(.+?)\s+(\d+)\s+more', text_lower)
#     if more_match:
#         product = more_match.group(1).strip()
#         qty = float(more_match.group(2))
#         # Don't extract price for "more" patterns
#         return product, qty, None
    
#     # Check for price change patterns
#     price_match = re.search(r'(.+?)\s+(?:price|rate)\s+(?:is|to|as)?\s*(\d+(?:\.\d+)?)', text_lower)
#     if price_match:
#         product = price_match.group(1).strip()
#         price = float(price_match.group(2))
#         return product, None, price
    
#     # Original extraction logic
#     # Extract price
#     price_patterns = [
#         r'for\s*(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
#         r'at\s*(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
#         r'price\s*(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
#         r'(?:rs|₹|inr)\s*(\d+(?:\.\d+)?)',
#     ]
    
#     for pattern in price_patterns:
#         match = re.search(pattern, text_lower)
#         if match:
#             try:
#                 price = float(match.group(1))
#                 text_lower = re.sub(pattern, '', text_lower, count=1)
#                 break
#             except (ValueError, TypeError):
#                 continue
    
#     # Extract quantity
#     numbers = re.findall(r'\d+(?:\.\d+)?', text_lower)
    
#     if numbers:
#         try:
#             if price is not None and len(numbers) >= 1:
#                 qty = float(numbers[0])
#                 text_lower = re.sub(r'\d+(?:\.\d+)?', '', text_lower, count=1)
#             elif price is None and len(numbers) == 1:
#                 if any(word in text_lower for word in ['for', 'at', 'price', 'rs', '₹', 'inr']):
#                     price = float(numbers[0])
#                 else:
#                     qty = float(numbers[0])
#             elif price is None and len(numbers) >= 2:
#                 qty = float(numbers[0])
#                 price = float(numbers[-1])
#         except (ValueError, TypeError):
#             # If conversion fails, use defaults
#             if qty is None:
#                 qty = 1.0
    
#     # Extract product
#     stop_words = {"i", "need", "want", "add", "order", "give", "me", "please", 
#                   "some", "the", "a", "an", "for", "at", "price", "rs", "₹", "inr",
#                   "more", "additional", "extra", "increase"}
    
#     words = re.findall(r'[a-z]+', text_lower)
#     filtered_words = []
#     for word in words:
#         if word not in stop_words and len(word) > 1:
#             filtered_words.append(word)
    
#     if filtered_words:
#         product = ' '.join(filtered_words).strip()
    
#     # Special handling
#     if not product:
#         patterns = [
#             r'(?:need|want|add|order)\s+([a-z]+(?:\s+[a-z]+)?)\s+(?:for|at|price)',
#             r'([a-z]+(?:\s+[a-z]+)?)\s+(?:for|at)\s+(?:rs|₹|inr|\d+)',
#         ]
        
#         for pattern in patterns:
#             match = re.search(pattern, text.lower())
#             if match:
#                 potential = match.group(1).strip()
#                 if potential not in stop_words and len(potential) > 1:
#                     product = potential
#                     break
    
#     # Special case: "i need 10 pen for 50 rs"
#     if product and price and qty is None:
#         start_match = re.match(r'^(\d+)\s+', text.lower())
#         if start_match:
#             try:
#                 qty = float(start_match.group(1))
#             except (ValueError, TypeError):
#                 qty = 1.0
#         else:
#             qty = 1.0
    
#     # Ensure we return at least quantity=1 if we have a product
#     if product and qty is None:
#         qty = 1.0
    
#     # Ensure price is set to something reasonable if not specified
#     if product and price is None and qty:
#         # Try to get price from database - USE THE SIMPLE VERSION
#         exists, db_price, stock = check_product_exists_simple(product)  # Changed to simple version
#         if exists and db_price:
#             price = float(db_price)
#         else:
#             price = 0.0  # Default price if not found
    
#     return product, qty, price

# def smart_product_match(user_input):
#     """Match product from input to database"""
#     products = get_product_options()
#     if not products:
#         return None
    
#     product, _, _ = extract_product_qty_price(user_input)
    
#     if product:
#         for p in products:
#             if p.lower() == product.lower():
#                 return p
        
#         for p in products:
#             if product.lower() in p.lower() or p.lower() in product.lower():
#                 return p
    
#     return product

# def get_ai_response(user_message, context_history):
#     """Get AI response"""
#     if not client:
#         user_lower = user_message.lower()
#         if any(word in user_lower for word in ["hi", "hello", "hey"]):
#             return "Hello! How can I help you today?"
#         elif "thank" in user_lower:
#             return "You're welcome!"
#         elif any(word in user_lower for word in ["bye", "goodbye"]):
#             return "Goodbye!"
#         else:
#             return "I can help you with invoices. What do you need?"
    
#     projects = get_projects()
#     parties = get_parties()
#     products = get_product_options()
    
#     system_prompt = f"""You are a helpful invoice assistant. Help users create invoices.
    
#     Available:
#     Projects: {', '.join([p[1] for p in projects[:3]]) if projects else 'None'}
#     Parties: {', '.join([p['name'] for p in parties[:3]]) if parties else 'None'}
#     Products: {', '.join(products[:3]) if products else 'None'}
    
#     Steps:
#     1. Select project
#     2. Select party (with address, pincode, GST info)
#     3. Select invoice type
#     4. Add products
#     5. Generate invoice with GST calculation
    
#     Be friendly and helpful. Keep responses short."""
    
#     messages = [
#         {"role": "system", "content": system_prompt},
#         *context_history[-4:],
#         {"role": "user", "content": user_message}
#     ]
    
#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=messages,
#             max_tokens=100,
#             temperature=0.7
#         )
#         return response.choices[0].message.content
#     except:
#         return "I can help you create invoices. What do you need?"

# def check_product_exists_with_id(product_name):
#     """Check if product exists in database and return id, price, stock"""
#     try:
#         with ENGINE.connect() as conn:
#             query = text("SELECT id, supply_rate, quantity FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
#             result = conn.execute(query, {"p": product_name})
#             row = result.fetchone()
#             if row:
#                 # Convert to appropriate types
#                 product_id = int(row[0]) if row[0] is not None else None
#                 price = float(row[1]) if row[1] is not None else None
#                 stock = float(row[2]) if row[2] is not None else None
#                 return True, product_id, price, stock
#             return False, None, None, None
#     except Exception as e:
#         print(f"Error checking product with ID: {e}")
#         return False, None, None, None

# # =========================
# # CHAT ENGINE (UPDATED VERSION) - WITH PROMPT COMMANDS FOR UPDATING
# # =========================

# def add_or_update_invoice_item(product_name, qty, price):
#     """Add or update item in invoice with all information and check stock"""
#     # Validate inputs
#     if qty is None or price is None:
#         return "invalid_input", None
    
#     try:
#         qty = float(qty)
#         price = float(price)
#     except (ValueError, TypeError):
#         return "invalid_input", None
    
#     # Check stock availability
#     available_stock = get_product_stock(product_name)
    
#     if available_stock is not None:
#         try:
#             available_stock = float(available_stock)
#         except (ValueError, TypeError):
#             available_stock = None
        
#         if available_stock is not None:
#             total_requested = qty
#             # Check if product already in invoice
#             for item in st.session_state.invoice:
#                 if item["item_description"].lower() == product_name.lower():
#                     item_qty = item.get("qty")
#                     if item_qty is not None:
#                         try:
#                             total_requested += float(item_qty)
#                         except (ValueError, TypeError):
#                             continue
            
#             # Check if stock is sufficient
#             if total_requested > available_stock:
#                 # Add to stock alerts
#                 st.session_state.stock_alert.append({
#                     "product": product_name,
#                     "requested": total_requested,
#                     "available": available_stock,
#                     "shortage": total_requested - available_stock
#                 })
#                 return "stock_insufficient", available_stock
    
#     # Check if item exists in invoice
#     for item in st.session_state.invoice:
#         if item["item_description"].lower() == product_name.lower():
#             # Update existing item
#             item["qty"] = qty
#             item["supply_rate"] = price
#             return "updated", None
    
#     # Add new item with all information
#     new_item = {
#         "item_description": product_name,
#         "qty": qty,
#         "supply_rate": price
#     }
    
#     # Add meta info if available
#     if st.session_state.invoice_meta["project_name"]:
#         new_item["project"] = st.session_state.invoice_meta["project_name"]
#     if st.session_state.invoice_meta["party_name"]:
#         new_item["party"] = st.session_state.invoice_meta["party_name"]
#     if st.session_state.invoice_meta["invoice_type"]:
#         new_item["invoice_type"] = st.session_state.invoice_meta["invoice_type"]
#     if st.session_state.invoice_meta["party_address"]:
#         new_item["party_address"] = st.session_state.invoice_meta["party_address"]
#     if st.session_state.invoice_meta["party_pincode"]:
#         new_item["party_pincode"] = st.session_state.invoice_meta["party_pincode"]
#     if st.session_state.invoice_meta["party_gst"]:
#         new_item["party_gst"] = st.session_state.invoice_meta["party_gst"]
    
#     st.session_state.invoice.append(new_item)
#     return "added", None


# def chat_engine(user_text):
#     text = user_text.lower().strip()
    
#     # Update context
#     st.session_state.ai_context.append({"role": "user", "content": user_text})

#     # ===========================================
#     # NEW: INCREASE QUANTITY COMMAND
#     # ===========================================
#     if text.startswith("increase") or text.startswith("add more"):
#         # Patterns to match:
#         # "increase pen by 5"
#         # "increase pen quantity by 5"
#         # "add more pen 5"
#         # "add 5 more pen"
        
#         patterns = [
#             r'(?:increase|add)\s+(.+?)\s+(?:by|)\s+(\d+)',
#             r'(?:increase|add)\s+(\d+)\s+more\s+(.+)',
#             r'(?:increase|add)\s+(.+?)\s+quantity\s+(?:by|)\s+(\d+)',
#             r'add\s+more\s+(.+?)\s+(\d+)',
#         ]
        
#         product = None
#         additional_qty = None
        
#         for pattern in patterns:
#             match = re.search(pattern, user_text, re.IGNORECASE)
#             if match:
#                 if len(match.groups()) == 2:
#                     # Check which pattern matched
#                     if pattern == r'(?:increase|add)\s+(\d+)\s+more\s+(.+)':
#                         additional_qty = int(match.group(1))
#                         product = match.group(2).strip()
#                     else:
#                         product = match.group(1).strip()
#                         additional_qty = int(match.group(2))
#                     break
        
#         # If pattern not matched, try alternative extraction
#         if not product:
#             # Extract product and number
#             numbers = re.findall(r'\d+', user_text)
#             words = re.findall(r'[a-zA-Z]+', user_text)
            
#             if numbers and len(words) >= 2:
#                 additional_qty = int(numbers[0])
#                 # Find product name (skip "increase", "add", "more", "quantity")
#                 stop_words = ["increase", "add", "more", "quantity", "by", "to", "additional"]
#                 product_words = []
#                 for word in words:
#                     if word.lower() not in stop_words:
#                         product_words.append(word)
                
#                 if product_words:
#                     product = ' '.join(product_words)
        
#         if product and additional_qty:
#             # Check if product exists in database
#             exists, db_price, current_stock = check_product_exists_simple(product)
            
#             if not exists:
#                 return f"❌ **{product}** not found in database."
            
#             # Check if product exists in current invoice
#             in_invoice = False
#             current_qty = 0
#             for item in st.session_state.invoice:
#                 if item["item_description"].lower() == product.lower():
#                     in_invoice = True
#                     current_qty = item["qty"]
#                     break
            
#             if not in_invoice:
#                 return f"❌ **{product}** not in current invoice. Add it first with 'add {product}'"
            
#             # Calculate new total quantity
#             new_total_qty = current_qty + additional_qty
            
#             # Check stock availability
#             if current_stock is not None:
#                 # Calculate total requested from all invoice items
#                 total_requested = new_total_qty
                
#                 # Check other invoice items for same product
#                 for item in st.session_state.invoice:
#                     if item["item_description"].lower() == product.lower():
#                         # Already counted in new_total_qty
#                         pass
                
#                 if total_requested > current_stock:
#                     return f"❌ **Stock Insufficient!** Only {current_stock} units available, need {total_requested} units."
            
#             # Update quantity in invoice
#             for item in st.session_state.invoice:
#                 if item["item_description"].lower() == product.lower():
#                     old_qty = item["qty"]
#                     item["qty"] = new_total_qty
                    
#                     response = f"✅ **Increased {product} quantity:**\n"
#                     response += f"• Invoice: {old_qty} → {new_total_qty} (+{additional_qty})\n"
                    
#                     # Update database stock (decrease by additional quantity)
#                     # Since invoice is not saved yet, we don't update database stock
#                     # Stock will be updated when invoice is generated
                    
#                     response += f"• Database price: ₹{db_price:,.2f}\n"
#                     if current_stock is not None:
#                         response += f"• Available stock: {current_stock} units\n"
#                         response += f"• Stock check: {current_stock} ≥ {new_total_qty} ✅"
                    
#                     return response
            
#             return f"❌ Error updating {product} in invoice"
        
#         return "❌ Please specify product and quantity. Example: 'increase pen by 5' or 'add 3 more notebook'"
    
#     # ===========================================
#     # NEW: DELETE ROW COMMAND
#     # ===========================================
#     if text.startswith("delete") or text.startswith("remove"):
#         # Patterns to match:
#         # "delete pen"
#         # "delete pen row"
#         # "remove pen from invoice"
#         # "remove pen item"
        
#         # Extract product name
#         patterns = [
#             r'(?:delete|remove)\s+(.+?)\s+(?:row|item|from invoice|line)',
#             r'(?:delete|remove)\s+(.+)'
#         ]
        
#         product = None
#         for pattern in patterns:
#             match = re.search(pattern, user_text, re.IGNORECASE)
#             if match:
#                 product = match.group(1).strip()
#                 break
        
#         # If pattern not matched, try simple extraction
#         if not product:
#             words = re.findall(r'[a-zA-Z]+', user_text)
#             stop_words = ["delete", "remove", "row", "item", "from", "invoice", "line"]
#             product_words = []
#             for word in words:
#                 if word.lower() not in stop_words:
#                     product_words.append(word)
            
#             if product_words:
#                 product = ' '.join(product_words)
        
#         if product:
#             # Check if product exists in invoice
#             in_invoice = False
#             for item in st.session_state.invoice:
#                 if item["item_description"].lower() == product.lower():
#                     in_invoice = True
#                     break
            
#             if not in_invoice:
#                 return f"❌ **{product}** not found in current invoice."
            
#             # Confirm deletion for important items
#             if len(st.session_state.invoice) == 1:
#                 st.session_state.pending_data = {"product": product}
#                 st.session_state.chat_stage = "CONFIRM_DELETE_LAST_ITEM"
#                 return f"⚠️ **This is the last item in your invoice.**\nAre you sure you want to delete '{product}'? (yes/no)"
            
#             # Remove the product
#             success, message = remove_product_from_invoice(product)
            
#             if success:
#                 # Update invoice totals display
#                 subtotal = 0
#                 for item in st.session_state.invoice:
#                     qty = item.get("qty")
#                     price = item.get("supply_rate")
#                     if qty is not None and price is not None:
#                         try:
#                             subtotal += float(qty) * float(price)
#                         except (ValueError, TypeError):
#                             continue
                
#                 response = f"✅ {message}\n\n"
#                 response += f"**Updated Invoice:**\n"
#                 response += f"• Items remaining: {len(st.session_state.invoice)}\n"
#                 response += f"• Subtotal: ₹{subtotal:,.2f}\n"
                
#                 if st.session_state.invoice:
#                     response += "\n**Remaining items:**\n"
#                     for i, item in enumerate(st.session_state.invoice, 1):
#                         response += f"{i}. {item['item_description']} - {item['qty']} × ₹{item['supply_rate']:,.2f}\n"
                
#                 return response
#             else:
#                 return message
        
#         return "❌ Please specify which product to delete. Example: 'delete pen' or 'remove notebook row'"



    
#     # ===========================================
#     # NEW: PROMPT COMMANDS FOR UPDATING INVOICE AND DATABASE
#     # ===========================================
    
#     # UPDATE QUANTITY IN INVOICE AND DATABASE
#     if text.startswith("update") or text.startswith("change"):
#         # Extract product and value
#         patterns = [
#             r'(?:update|change)\s+(.+?)\s+(?:quantity|qty|qty\.)\s+(?:to|by|as)\s+(\d+(?:\.\d+)?)',
#             r'(?:update|change)\s+(.+?)\s+(?:price|rate)\s+(?:to|by|as)\s+(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
#             r'set\s+(.+?)\s+(?:quantity|qty|qty\.)\s+(?:to|as)\s+(\d+(?:\.\d+)?)',
#             r'set\s+(.+?)\s+(?:price|rate)\s+(?:to|as)\s+(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
#         ]
        
#         for pattern in patterns:
#             match = re.search(pattern, user_text, re.IGNORECASE)
#             if match:
#                 product = match.group(1).strip()
#                 value = float(match.group(2))
                
#                 # Determine what to update
#                 is_price = any(word in user_text.lower() for word in ["price", "rate"])
#                 is_quantity = any(word in user_text.lower() for word in ["quantity", "qty", "qty."])
                
#                 # Check if product exists in database - FIX THIS LINE
#                 exists, db_price, db_stock = check_product_exists_simple(product)  # Use the 3-value version
                
#                 if not exists:
#                     return f"❌ **{product}** not found in database."
                
#                 # Prepare response based on what's being updated
#                 if is_quantity:
#                     # Update quantity in invoice
#                     updated_in_invoice = False
#                     for item in st.session_state.invoice:
#                         if item["item_description"].lower() == product.lower():
#                             old_qty = item["qty"]
#                             item["qty"] = value
#                             updated_in_invoice = True
#                             break
                    
#                     # Update database stock (set new quantity)
#                     success, message = update_product_stock(product, value)
                    
#                     response = f"✅ **Updated {product}:**\n"
#                     if updated_in_invoice:
#                         response += f"• Invoice quantity: {old_qty} → {value}\n"
#                     response += f"• Database stock: {db_stock} → {value}\n"
                    
#                     # Update stock alert if needed
#                     if value > db_stock:
#                         response += f"⚠️ **Note:** New quantity ({value}) is higher than old stock ({db_stock})"
                    
#                     return response
                
#                 elif is_price:
#                     # Update price in invoice
#                     updated_in_invoice = False
#                     for item in st.session_state.invoice:
#                         if item["item_description"].lower() == product.lower():
#                             old_price = item["supply_rate"]
#                             item["supply_rate"] = value
#                             updated_in_invoice = True
#                             break
                    
#                     # Update database price
#                     success, message = update_product_price(product, value)
                    
#                     response = f"✅ **Updated {product} price:**\n"
#                     if updated_in_invoice:
#                         response += f"• Invoice price: ₹{old_price:,.2f} → ₹{value:,.2f}\n"
#                     response += f"• Database price: ₹{db_price:,.2f} → ₹{value:,.2f}\n"
                    
#                     # Calculate percentage change
#                     if db_price and db_price > 0:
#                         price_diff = ((value - db_price) / db_price) * 100
#                         response += f"• Change: {price_diff:+.1f}%"
                    
#                     return response
        
#         # If pattern not matched, try alternative extraction
#         product = smart_product_match(user_text)
#         if product:
#             # Extract numbers from text
#             numbers = re.findall(r'\d+(?:\.\d+)?', user_text)
#             if numbers:
#                 value = float(numbers[0])
                
#                 # Guess what to update based on context
#                 if any(word in user_text.lower() for word in ["price", "rate", "₹", "rs", "inr"]):
#                     # Update price
#                     exists, db_price, db_stock = check_product_exists(product)
#                     if exists:
#                         # Update invoice
#                         updated = False
#                         for item in st.session_state.invoice:
#                             if item["item_description"].lower() == product.lower():
#                                 old_price = item["supply_rate"]
#                                 item["supply_rate"] = value
#                                 updated = True
#                                 break
                        
#                         # Update database
#                         success, message = update_product_price(product, value)
                        
#                         response = f"✅ **Updated {product} price to ₹{value:,.2f}**\n"
#                         if updated:
#                             response += f"• Invoice updated\n"
#                         response += f"• Database updated (from ₹{db_price:,.2f})"
#                         return response
#                     else:
#                         return f"❌ **{product}** not found in database."
#                 else:
#                     # Update quantity
#                     exists, db_price, db_stock = check_product_exists(product)
#                     if exists:
#                         # Update invoice
#                         updated = False
#                         for item in st.session_state.invoice:
#                             if item["item_description"].lower() == product.lower():
#                                 old_qty = item["qty"]
#                                 item["qty"] = value
#                                 updated = True
#                                 break
                        
#                         # Update database
#                         success, message = update_product_stock(product, value)
                        
#                         response = f"✅ **Updated {product} quantity to {value}**\n"
#                         if updated:
#                             response += f"• Invoice updated\n"
#                         response += f"• Database stock updated (from {db_stock})"
#                         return response
#                     else:
#                         return f"❌ **{product}** not found in database."
                    

#     # Add this to chat engine for testing
#     if text == "test type mapping":
#         test_types = ["purchase", "purchase_order", "sales", "credit", "debit", "delivery_challan"]
        
#         response = "🔍 **Type Mapping Test:**\n\n"
#         for t in test_types:
#             code = get_type_code(t)
#             response += f"• **'{t}'** → **'{code}'**\n"
#             response += f"  Example: ICE/2025-2026/{code}/0001\n\n"
        
#         # Also test with current session type
#         current_type = st.session_state.invoice_meta.get("invoice_type")
#         if current_type:
#             current_code = get_type_code(current_type)
#             response += f"\n**Current session type:** '{current_type}' → '{current_code}'\n"
        
#         return response                
    
#     # ===========================================
#     # PROACTIVE PRICE COMPARISON DETECTION
#     # ===========================================
#     # Check if user is mentioning prices for existing products
#     if not st.session_state.chat_stage and not st.session_state.awaiting_choice:
#         # Try to extract product and price from natural language
#         product, qty, price = extract_product_qty_price(user_text)
        
#         if product and price:
#             exists, db_price, stock = check_product_exists_simple(product)  # This should be correct
            
#             if exists and db_price:
#                 # FIX: Convert both to float for calculation
#                 try:
#                     db_price_float = float(db_price)
#                     price_float = float(price)
#                     price_diff = ((price_float - db_price_float) / db_price_float) * 100
#                 except (ValueError, TypeError):
#                     # If conversion fails, skip price comparison
#                     price_diff = 0
                
#                 # Show notification for significant differences
#                 if abs(price_diff) > 5:  # More than 5% difference
#                     if price_float < db_price_float:
#                         # Lower price detected
#                         st.session_state.pending_data = {
#                             "product": product,
#                             "qty": qty or 1,
#                             "user_price": price_float,
#                             "db_price": db_price_float,
#                             "diff_percent": abs(price_diff),
#                             "from_natural_language": True
#                         }
                        
#                         if price_diff < -20:  # More than 20% lower
#                             response = f"⚠️ **Alert: Very Low Price Mentioned!**\n"
#                             response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
#                             response += f"Database price: ₹{db_price_float:,.2f}\n"
#                             response += f"**Difference:** {abs(price_diff):.1f}% lower\n\n"
#                             response += "Options:\n"
#                             response += "• Type 'add' to add with your price\n"
#                             response += "• Type 'use db' to use database price\n"
#                             response += "• Type 'check' to verify stock\n"
#                             st.session_state.chat_stage = "PRICE_ALERT_LOW"
#                         else:
#                             response = f"📉 **Note: Lower Price Mentioned**\n"
#                             response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
#                             response += f"Database price: ₹{db_price_float:,.2f}\n"
#                             response += f"({abs(price_diff):.1f}% lower)\n\n"
#                             response += "Shall I use your price? (yes/no)"
#                             st.session_state.chat_stage = "PRICE_ALERT_SMALL_LOW"
                        
#                         return response
                    
#                     elif price_float > db_price_float:
#                         # Higher price detected
#                         st.session_state.pending_data = {
#                             "product": product,
#                             "qty": qty or 1,
#                             "user_price": price_float,
#                             "db_price": db_price_float,
#                             "diff_percent": price_diff,
#                             "from_natural_language": True
#                         }
                        
#                         if price_diff > 50:  # More than 50% higher
#                             response = f"💰 **Alert: High Price Mentioned!**\n"
#                             response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
#                             response += f"Database price: ₹{db_price_float:,.2f}\n"
#                             response += f"**Difference:** {price_diff:.1f}% higher\n\n"
#                             response += "Options:\n"
#                             response += "• Type 'add' to add with higher price\n"
#                             response += "• Type 'update' to update database price\n"
#                             response += "• Type 'use db' to use database price\n"
#                             st.session_state.chat_stage = "PRICE_ALERT_HIGH"
#                         else:
#                             response = f"📈 **Note: Higher Price Mentioned**\n"
#                             response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
#                             response += f"Database price: ₹{db_price_float:,.2f}\n"
#                             response += f"({price_diff:.1f}% higher)\n\n"
#                             response += "Update database to new price? (update/use db)"
#                             st.session_state.chat_stage = "PRICE_ALERT_SMALL_HIGH"
                        
#                         return response
                    
#                     elif price_float > db_price_float:
#                         # Higher price detected
#                         st.session_state.pending_data = {
#                             "product": product,
#                             "qty": qty or 1,
#                             "user_price": price_float,
#                             "db_price": db_price_float,
#                             "diff_percent": price_diff,
#                             "from_natural_language": True
#                         }
                        
#                         if price_diff > 50:  # More than 50% higher
#                             response = f"💰 **Alert: High Price Mentioned!**\n"
#                             response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
#                             response += f"Database price: ₹{db_price_float:,.2f}\n"
#                             response += f"**Difference:** {price_diff:.1f}% higher\n\n"
#                             response += "Options:\n"
#                             response += "• Type 'add' to add with higher price\n"
#                             response += "• Type 'update' to update database price\n"
#                             response += "• Type 'use db' to use database price\n"
#                             st.session_state.chat_stage = "PRICE_ALERT_HIGH"
#                         else:
#                             response = f"📈 **Note: Higher Price Mentioned**\n"
#                             response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
#                             response += f"Database price: ₹{db_price_float:,.2f}\n"
#                             response += f"({price_diff:.1f}% higher)\n\n"
#                             response += "Update database to new price? (update/use db)"
#                             st.session_state.chat_stage = "PRICE_ALERT_SMALL_HIGH"
                        
#                         return response
    
#     # ===========================================
#     # HANDLE PRICE ALERT RESPONSES
#     # ===========================================
#     if st.session_state.chat_stage == "PRICE_ALERT_LOW":
#         if text in ["add", "yes", "y", "ok"]:
#             p = st.session_state.pending_data
#             # Check stock
#             stock = get_product_stock(p["product"])
#             if stock is not None and p["qty"] > stock:
#                 return f"❌ **Stock Insufficient!** Only {stock} units available for {p['product']}"
            
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}** (DB: ₹{p['db_price']}). Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}** (DB: ₹{p['db_price']})"
        
#         elif text in ["use db", "db", "database", "no", "n"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
#         elif text == "check":
#             p = st.session_state.pending_data
#             stock = get_product_stock(p["product"])
#             if stock is not None:
#                 return f"📦 **Stock for {p['product']}:** {stock} units available\n\nNow type 'add' or 'use db'"
#             else:
#                 return f"❌ **{p['product']}** not found in database"
        
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Cancelled price check."
    
#     elif st.session_state.chat_stage == "PRICE_ALERT_SMALL_LOW":
#         if text in ["yes", "y", "ok", "add"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}**. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}**"
        
#         elif text in ["no", "n", "db"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Using database price."
    
#     elif st.session_state.chat_stage == "PRICE_ALERT_HIGH":
#         if text in ["add", "yes", "y"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}**. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}**"
        
#         elif text == "update":
#             p = st.session_state.pending_data
#             success, message = update_product_price(p["product"], p["user_price"])
#             if success:
#                 action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#                 st.session_state.chat_stage = None
                
#                 if action == "stock_insufficient":
#                     return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#                 elif action == "updated":
#                     total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                                 if item['item_description'].lower() == p["product"].lower())
#                     return f"✅ **Database price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}. Total now {total_qty}"
#                 else:
#                     return f"✅ **Database price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}"
#             else:
#                 return f"❌ {message}"
        
#         elif text in ["use db", "db", "database", "no", "n"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Using database price."
    
#     elif st.session_state.chat_stage == "PRICE_ALERT_SMALL_HIGH":
#         if text == "update":
#             p = st.session_state.pending_data
#             success, message = update_product_price(p["product"], p["user_price"])
#             if success:
#                 action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#                 st.session_state.chat_stage = None
                
#                 if action == "stock_insufficient":
#                     return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#                 elif action == "updated":
#                     total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                                 if item['item_description'].lower() == p["product"].lower())
#                     return f"✅ **Price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}. Total now {total_qty}"
#                 else:
#                     return f"✅ **Price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}"
#             else:
#                 return f"❌ {message}"
        
#         elif text in ["use db", "db", "database", "no", "n"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Using database price."
    
#     # ===========================================
#     # EXISTING FUNCTIONALITY (REST OF THE CHAT ENGINE)
#     # ===========================================
    
#     # Greetings
#     if text in ["hi", "hello", "hey"]:
#         response = "👋 Hello! I can help you create invoices with automatic GST calculation. Type 'generate invoice' to start or 'view invoice [number]' to see old invoices."
#         st.session_state.ai_context.append({"role": "assistant", "content": response})
#         return response
    
#     # STOCK MANAGEMENT COMMANDS
#     if text.startswith("add stock") or text.startswith("increase stock"):
#         # Extract product and quantity
#         match = re.search(r'add stock\s+(.+?)\s+by\s+(\d+)', user_text, re.IGNORECASE)
#         if not match:
#             match = re.search(r'increase stock\s+(.+?)\s+by\s+(\d+)', user_text, re.IGNORECASE)
        
#         if not match:
#             # Try alternative pattern
#             numbers = re.findall(r'\d+', user_text)
#             words = re.findall(r'[a-zA-Z]+', user_text)
            
#             if len(numbers) >= 1 and len(words) >= 3:
#                 product = ' '.join(words[2:])  # Skip "add stock"
#                 qty = int(numbers[0])
#                 success, message = increase_product_stock(product, qty)
#                 return message
        
#         if match:
#             product = match.group(1).strip()
#             qty = int(match.group(2))
#             success, message = increase_product_stock(product, qty)
#             return message
        
#         return "❌ Please specify product and quantity. Example: 'add stock pen by 10' or 'increase stock notebook by 5'"
    
#     if text.startswith("check stock"):
#         # Extract product name
#         product_match = re.search(r'check stock\s+(.+)', user_text, re.IGNORECASE)
#         if product_match:
#             product_name = product_match.group(1).strip()
#             stock = get_product_stock(product_name)
#             if stock is not None:
#                 return f"📦 **Stock for {product_name}:** {stock} units"
#             else:
#                 return f"❌ Product '{product_name}' not found in database"
#         else:
#             return "❌ Please specify product name. Example: 'check stock pen'"
    
#     if text.startswith("set stock") or text.startswith("update stock"):
#         # Extract product and quantity
#         match = re.search(r'(?:set|update) stock\s+(.+?)\s+to\s+(\d+)', user_text, re.IGNORECASE)
#         if match:
#             product = match.group(1).strip()
#             qty = int(match.group(2))
#             success, message = update_product_stock(product, qty)
#             return message
#         return "❌ Please specify product and quantity. Example: 'set stock pen to 50'"
    

#     # ===========================================
#     # NEW: CONFIRM DELETE LAST ITEM
#     # ===========================================
#     if st.session_state.chat_stage == "CONFIRM_DELETE_LAST_ITEM":
#         if text in ["yes", "y", "confirm", "ok", "okay"]:
#             p = st.session_state.pending_data
#             success, message = remove_product_from_invoice(p["product"])
#             st.session_state.chat_stage = None
            
#             if success:
#                 return f"✅ {message}\n\nInvoice is now empty. Add new items to continue."
#             else:
#                 return message
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Deletion cancelled. Item kept in invoice."

    
#     # PRICE VALIDATION CONFIRMATION
#     if st.session_state.chat_stage == "CONFIRM_LOW_PRICE":
#         if text in ["yes", "ok", "okay", "confirm", "y", "proceed"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **lower price ₹{p['user_price']}** (DB: ₹{p['db_price']}). Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **lower price ₹{p['user_price']}** (DB: ₹{p['db_price']})"
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Order cancelled. Using database price."

#     if st.session_state.chat_stage == "CONFIRM_HIGH_PRICE":
#         if text in ["yes", "ok", "okay", "confirm", "y"]:
#             p = st.session_state.pending_data
#             # Optionally update database price
#             if p.get("update_db", False):
#                 success, _ = update_product_price(p["product"], p["user_price"])
            
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 msg = f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}** (DB: ₹{p['db_price']}). Total now {total_qty}"
#                 if p.get("update_db", False):
#                     msg += f"\n✅ Database price updated to ₹{p['user_price']}"
#                 return msg
#             else:
#                 msg = f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}** (DB: ₹{p['db_price']})"
#                 if p.get("update_db", False):
#                     msg += f"\n✅ Database price updated to ₹{p['user_price']}"
#                 return msg
#         elif text in ["no", "cancel", "n", "use db"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                             if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Using database price."
        
#     # In the chat engine, add a debug command for invoices:
#     if text.startswith("debug invoices"):
#         invoices = debug_all_invoice_numbers()
#         if isinstance(invoices, str):
#             return f"❌ {invoices}"
        
#         response = "🔍 **All Invoices in Database:**\n\n"
#         for inv in invoices:
#             response += f"• **ID:** {inv['id']}\n"
#             response += f"  **invoiceNumber:** '{inv['invoiceNumber']}'\n"
#             response += f"  **invoice_number_generated:** '{inv['invoice_number_generated']}'\n"
#             response += f"  **Type:** {inv['type']}, **Date:** {inv['date']}, **Total:** ₹{inv['total']:,.2f}\n"
#             response += f"  **Status:** {inv['status']}, **Created:** {inv['createdAt']}\n"
#             response += "  ---\n"
        
#         response += f"\nTotal shown: {len(invoices)}"
#         return response
    
#     # VIEW OLD INVOICE
#     if text.startswith("view invoice") or text.startswith("show invoice"):
#         # Extract the complete invoice number including special characters
#         match = re.search(r'(?:view invoice|show invoice)\s+(.+)', user_text, re.IGNORECASE)
        
#         if not match:
#             return "❌ Please provide an invoice number. Example: 'view invoice ICE/25-26/INV/0018'"
        
#         invoice_no = match.group(1).strip()
        
#         # First try to get the invoice
#         invoice_data = get_invoice_by_number(invoice_no)
        
#         if not invoice_data:
#             # Try to get list of similar invoices
#             try:
#                 with ENGINE.connect() as conn:
#                     # Get all invoice numbers
#                     query = text("""
#                         SELECT DISTINCT invoiceNumber 
#                         FROM invoices 
#                         WHERE invoiceNumber IS NOT NULL 
#                         ORDER BY invoiceNumber
#                     """)
#                     result = conn.execute(query)
#                     all_invoices = [row[0] for row in result.fetchall() if row[0]]
                    
#                     # Find similar invoices
#                     similar = []
#                     for inv in all_invoices:
#                         if invoice_no.lower() in str(inv).lower():
#                             similar.append(inv)
#                         elif str(inv).lower().startswith(invoice_no.lower()):
#                             similar.append(inv)
                    
#                     if similar:
#                         response = f"❌ **Invoice '{invoice_no}' not found.**\n\n"
#                         response += "**Similar invoices in database:**\n"
#                         for inv in similar[:5]:  # Show top 5 matches
#                             response += f"• {inv}\n"
#                         response += "\nTry one of these exact invoice numbers."
#                     else:
#                         response = f"❌ **Invoice '{invoice_no}' not found in database.**\n\n"
#                         response += "**Available invoice numbers:**\n"
#                         for inv in all_invoices[:10]:  # Show first 10
#                             response += f"• {inv}\n"
#                         if len(all_invoices) > 10:
#                             response += f"\n... and {len(all_invoices) - 10} more"
#                         response += "\n\nType 'debug invoices' to see all invoices with details."
                    
#                     return response
#             except Exception as e:
#                 return f"❌ Invoice '{invoice_no}' not found. Error: {str(e)}"
        
#         # Store old invoice data in session
#         st.session_state.viewing_old_invoice = True
#         st.session_state.old_invoice_data = invoice_data
        
#         response = f"✅ **Invoice #{invoice_data['header']['invoice_no']} Found!**\n\n"
#         response += f"**Project:** {invoice_data['header']['project_name']}\n"
#         response += f"**Party:** {invoice_data['header']['party_name']}\n"
#         response += f"**Type:** {invoice_data['header']['invoice_type']}\n"
#         response += f"**Date:** {invoice_data['header']['invoice_date']}\n"
#         response += f"**Subtotal:** ₹{invoice_data['header']['subtotal']:,.2f}\n"
#         response += f"**Tax (GST):** ₹{invoice_data['header']['tax']:,.2f}\n"
#         response += f"**Grand Total:** ₹{invoice_data['header']['grand_total']:,.2f}\n"
#         response += f"**Items:** {len(invoice_data['items'])}\n\n"
#         response += "Check the invoice details below 👇"
        
#         return response
    
#     # LIST ALL INVOICES
#     if text.startswith("list invoices") or text == "invoices":
#         invoices = get_all_invoices()
#         if not invoices:
#             return "❌ No invoices found in database."
        
#         response = "📋 **Available Invoices:**\n\n"
#         for i, inv in enumerate(invoices, 1):
#             response += f"{i}. **#{inv['invoice_no']}** - Date: {inv['invoice_date']} - Type: {inv['invoice_type']} - Total: ₹{inv['grand_total']:,.2f}\n"
        
#         response += "\nTo view an invoice, type 'view invoice [number]'"
#         return response
    
#     # GENERATE INVOICE FLOW START
#     if "generate invoice" in text or "create invoice" in text:
#         projects = get_projects()
#         if not projects:
#             return "❌ No projects found in database. Please add projects first."
        
#         st.session_state.invoice_flow = "GENERATING"
#         st.session_state.choice_type = "PROJECT"
#         st.session_state.choice_options = projects
#         st.session_state.awaiting_choice = True
        
#         response = "🏗️ **Select a Project:**\n\n"
#         for i, (id, name) in enumerate(projects, 1):
#             response += f"{i}. {name}\n"
#         response += "\nReply with number (1, 2, 3...)"
        
#         return response
    
#     # DEBUG COMMANDS
#     if text.startswith("debug tables"):
#         tables = debug_database_tables()
#         if isinstance(tables, str):
#             return f"❌ {tables}"
        
#         response = "🔍 **Database Tables:**\n\n"
#         for i, table in enumerate(tables, 1):
#             response += f"{i}. {table}\n"
        
#         return response
    
#     if text.startswith("debug table"):
#         # Extract table name
#         match = re.search(r'debug table\s+(.+)', user_text, re.IGNORECASE)
#         if not match:
#             return "❌ Please provide a table name. Example: 'debug table parties'"
        
#         table_name = match.group(1).strip()
#         debug_info = debug_table_structure(table_name)
        
#         if isinstance(debug_info, str):
#             return f"❌ {debug_info}"
        
#         response = f"🔍 **Table Structure: {table_name}**\n\n"
#         response += "**Columns:**\n"
#         for col in debug_info["columns"]:
#             response += f"• {col['field']} ({col['type']}) - Null: {col['null']}\n"
        
#         response += "\n**Sample Data (first 3 rows):**\n"
#         for i, row in enumerate(debug_info["sample_data"], 1):
#             response += f"{i}. {row}\n"
        
#         return response
    
#     if text.startswith("debug search"):
#         invoices = debug_search_invoices()
#         if isinstance(invoices, str):
#             return f"❌ {invoices}"
        
#         response = "🔍 **Debug - All Invoice Numbers in Database:**\n\n"
#         for inv in invoices:
#             response += f"• **invoice_number_generated:** '{inv['invoice_number_generated']}' "
#             response += f"(UPPER: '{inv['upper_generated']}')\n"
#             response += f"  **invoiceNumber:** '{inv['invoiceNumber']}' "
#             response += f"(UPPER: '{inv['upper_number']}')\n"
#             response += f"  **Date:** {inv['date']}, **Type:** {inv['type']}, **Total:** ₹{inv['total']:,.2f}\n"
#             response += "  ---\n"
        
#         response += f"\nTotal found: {len(invoices)}"
#         return response
    
#     if text.startswith("check invoice"):
#         # Extract invoice number
#         match = re.search(r'check invoice\s+(.+)', user_text, re.IGNORECASE)
#         if not match:
#             return "❌ Please provide an invoice number. Example: 'check invoice ICE/25-26/PO/020'"
        
#         invoice_no = match.group(1).strip()
        
#         try:
#             with ENGINE.connect() as conn:
#                 # Check if invoice exists in invoiceNumber column
#                 query = text("""
#                     SELECT invoiceNumber, invoice_number_generated, type, date, total, status, clientId, project_id
#                     FROM invoices 
#                     WHERE invoiceNumber = :no
#                     LIMIT 1
#                 """)
#                 result = conn.execute(query, {"no": invoice_no})
#                 row = result.fetchone()
                
#                 if row:
#                     response = f"✅ **Invoice Found in Database:**\n\n"
#                     response += f"**invoiceNumber:** '{row[0]}'\n"
#                     response += f"**invoice_number_generated:** '{row[1]}'\n"
#                     response += f"**Type:** {row[2]}\n"
#                     response += f"**Date:** {row[3]}\n"
#                     response += f"**Total:** ₹{float(row[4]) if row[4] else 0:,.2f}\n"
#                     response += f"**Status:** {row[5]}\n"
#                     response += f"**Client ID:** {row[6]}\n"
#                     response += f"**Project ID:** {row[7]}"
#                     return response
#                 else:
#                     # Try with LIKE search
#                     query = text("""
#                         SELECT invoiceNumber, invoice_number_generated, type, date, total, status
#                         FROM invoices 
#                         WHERE invoiceNumber LIKE :pattern
#                         LIMIT 5
#                     """)
#                     result = conn.execute(query, {"pattern": f"%{invoice_no}%"})
#                     rows = result.fetchall()
                    
#                     if rows:
#                         response = f"🔍 **Similar invoices found for '{invoice_no}':**\n\n"
#                         for r in rows:
#                             response += f"• **{r[0]}** - {r[2]} - {r[3]} - ₹{float(r[4]) if r[4] else 0:,.2f}\n"
#                         return response
#                     else:
#                         return f"❌ Invoice **{invoice_no}** not found in invoiceNumber column."
#         except Exception as e:
#             return f"❌ Error: {e}"
    
#     if text.startswith("search invoices"):
#         search_term = text.replace("search invoices", "").strip()
#         if not search_term:
#             return "❌ Please provide a search term"
        
#         try:
#             with ENGINE.connect() as conn:
#                 query = text("""
#                     SELECT invoiceNumber, type, date, total, status, clientId, project_id
#                     FROM invoices 
#                     WHERE invoiceNumber LIKE :pattern
#                     ORDER BY createdAt DESC
#                     LIMIT 10
#                 """)
#                 result = conn.execute(query, {"pattern": f"%{search_term}%"})
#                 rows = result.fetchall()
                
#                 if not rows:
#                     return f"❌ No invoices found containing '{search_term}'"
                
#                 response = f"🔍 **Invoices containing '{search_term}':**\n\n"
#                 for i, row in enumerate(rows, 1):
#                     response += f"{i}. **{row[0]}** - {row[1]} - {row[2]} - ₹{float(row[3]) if row[3] else 0:,.2f} - {row[4]}\n"
#                     response += f"   Client ID: {row[5]}, Project ID: {row[6]}\n"
                
#                 response += f"\n**Total found:** {len(rows)}"
#                 return response
#         except Exception as e:
#             return f"❌ Error: {e}"
    
#     # HANDLE CHOICE SELECTIONS
#     if st.session_state.awaiting_choice and text.isdigit():
#         idx = int(text) - 1
        
#         if idx < 0 or idx >= len(st.session_state.choice_options):
#             return "❌ Invalid selection. Please choose a valid number."
        
#         if st.session_state.choice_type == "PROJECT":
#             # Project selected
#             project_id, project_name = st.session_state.choice_options[idx]
#             st.session_state.invoice_meta["project_id"] = project_id
#             st.session_state.invoice_meta["project_name"] = project_name
            
#             # Get parties with address info
#             parties = get_parties()
#             if not parties:
#                 st.session_state.awaiting_choice = False
#                 st.session_state.choice_type = None
#                 return "❌ No parties found in database. Please add parties first."
            
#             st.session_state.choice_type = "PARTY"
#             st.session_state.choice_options = parties
#             st.session_state.awaiting_choice = True
            
#             response = f"✅ **Project Selected:** {project_name}\n\n"
#             response += "👥 **Select a Party:**\n\n"
#             for i, party in enumerate(parties, 1):
#                 # Safely display party info
#                 party_display = f"{i}. {party['name']}"
                
#                 # Add pincode if available
#                 if party.get("pincode"):
#                     party_display += f" [{party['pincode']}]"
                
#                 # Add truncated address if available
#                 if party.get("address"):
#                     address = party['address']
#                     if len(address) > 30:
#                         party_display += f" - {address[:30]}..."
#                     else:
#                         party_display += f" - {address}"
                
#                 response += party_display + "\n"
#             response += "\nReply with number (1, 2, 3...)"
            
#             return response
        
#         elif st.session_state.choice_type == "PARTY":
#             # Party selected - GET ADDRESS, PINCODE, GST INFO
#             party = st.session_state.choice_options[idx]
#             st.session_state.invoice_meta["party_id"] = party["id"]
#             st.session_state.invoice_meta["party_name"] = party["name"]
#             st.session_state.invoice_meta["party_address"] = party.get("address")
#             st.session_state.invoice_meta["party_pincode"] = party.get("pincode")
#             st.session_state.invoice_meta["party_gst"] = party.get("gst")
            
#             # Show party details including address
#             party_details = f"✅ **Party Selected:** {party['name']}\n"
#             if party.get("address"):
#                 party_details += f"**Address:** {party['address']}\n"
#             if party.get("pincode"):
#                 party_details += f"**Pincode:** {party['pincode']}\n"
#             if party.get("gst"):
#                 party_details += f"**GST:** {party['gst']}\n"
            
#             # Get invoice types
#             invoice_types = get_invoice_types()
#             st.session_state.choice_type = "INVOICE_TYPE"
#             st.session_state.choice_options = invoice_types
#             st.session_state.awaiting_choice = True
            
#             response = party_details + "\n"
#             response += "📄 **Select Invoice Type:**\n\n"
#             for i, inv_type in enumerate(invoice_types, 1):
#                 response += f"{i}. {inv_type}\n"
#             response += "\nReply with number (1, 2, 3...)"
            
#             return response
        
#         # In the chat engine, find the INVOICE_TYPE selection part and update it:
#         elif st.session_state.choice_type == "INVOICE_TYPE":
#             # Invoice type selected - extract just the base type (before parentheses)
#             invoice_type_with_code = st.session_state.choice_options[idx]
            
#             # Extract just the type name (before parentheses if present)
#             if "(" in invoice_type_with_code:
#                 # Extract the part before parentheses
#                 invoice_type = invoice_type_with_code.split("(")[0].strip()
#             else:
#                 invoice_type = invoice_type_with_code.strip()
            
#             # Store the clean type
#             st.session_state.invoice_meta["invoice_type"] = invoice_type
            
#             # Get the type code for display
#             type_code = get_type_code(invoice_type)
            
#             # Clear choice state
#             st.session_state.awaiting_choice = False
#             st.session_state.choice_type = None
#             st.session_state.choice_options = []
#             st.session_state.invoice_flow = None
            
#             response = f"✅ **Invoice Setup Complete!**\n\n"
#             response += f"**Project:** {st.session_state.invoice_meta['project_name']}\n"
#             response += f"**Party:** {st.session_state.invoice_meta['party_name']}\n"
            
#             # Show address if available
#             if st.session_state.invoice_meta["party_address"]:
#                 response += f"**Address:** {st.session_state.invoice_meta['party_address']}\n"
            
#             # Extract pincode from address if not in party_pincode
#             pincode = st.session_state.invoice_meta["party_pincode"]
            
#             # If no pincode in party data, try to extract from address
#             if not pincode and st.session_state.invoice_meta["party_address"]:
#                 address = st.session_state.invoice_meta["party_address"]
#                 # Look for 6-digit number in address
#                 pincode_match = re.search(r'(\d{6})', address)
#                 if pincode_match:
#                     pincode = pincode_match.group(1)
#                     st.session_state.invoice_meta["party_pincode"] = pincode
            
#             # Show pincode if found
#             if pincode:
#                 response += f"**Pincode:** {pincode}\n"
#                 # Show GST type based on pincode
#                 gst_info = get_gst_rate_from_pincode(pincode)
#                 response += f"**GST Type:** {gst_info['type']} ({gst_info['total_gst_rate']}%)\n"
            
#             # Show GST number only if it looks like a GST
#             if st.session_state.invoice_meta["party_gst"]:
#                 gst = st.session_state.invoice_meta["party_gst"]
#                 if re.match(r'^[0-9A-Z]{10,}$', gst):
#                     response += f"**GST Number:** {gst}\n"
            
#             response += f"**Invoice Type:** {invoice_type} ({type_code})\n\n"
#             response += "Now you can add products. Example: 'i need 10 pen for 50 rs'"
            
#             return response
    
#     # PRODUCT PRICE CHANGE CONFIRMATION
#     if st.session_state.chat_stage == "CONFIRM_PRICE_CHANGE":
#         if text in ["yes", "ok", "okay", "confirm", "y"]:
#             p = st.session_state.pending_data
#             success, message = update_product_price(p["product"], p["new_price"])
#             if success:
#                 for item in st.session_state.invoice:
#                     if item["item_description"].lower() == p["product"].lower():
#                         item["supply_rate"] = p["new_price"]
                
#                 st.session_state.chat_stage = None
#                 return f"✅ Price of **{p['product']}** updated to ₹{p['new_price']}"
#             else:
#                 st.session_state.chat_stage = None
#                 return f"❌ {message}"
#         else:
#             st.session_state.chat_stage = None
#             return "❌ Price update cancelled."
    
#     # CONFIRM PRICE CHANGE FOR ORDER
#     if st.session_state.chat_stage == "CONFIRM_PRICE_CHANGE_FOR_ORDER":
#         if text in ["yes", "ok", "okay", "confirm", "y"]:
#             p = st.session_state.pending_data
#             success, _ = update_product_price(p["product"], p["user_price"])
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                               if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Price updated to ₹{p['user_price']} and quantity increased by {p['qty']}. Total now {total_qty}"
#             else:
#                 return f"✅ Price updated to ₹{p['user_price']} and added {p['qty']} {p['product']} to invoice"
#         elif text in ["no", "cancel", "n"]:
#             p = st.session_state.pending_data
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
#             st.session_state.chat_stage = None
            
#             if action == "stock_insufficient":
#                 return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                               if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ Quantity increased by {p['qty']} at database price ₹{p['db_price']}. Total now {total_qty}"
#             else:
#                 return f"✅ Added {p['qty']} {p['product']} at database price ₹{p['db_price']} to invoice"
#         else:
#             st.session_state.chat_stage = None
#             return "Using database price."
    
#     # ADD PRODUCT TO DB CONFIRMATION
#     if st.session_state.chat_stage == "ADD":
#         if text in ["yes", "ok", "okay", "confirm", "y"]:
#             p = st.session_state.pending_data
#             # Ask for initial stock
#             if "stock" not in p:
#                 st.session_state.pending_data["stock"] = 0
#                 st.session_state.chat_stage = "ASK_INITIAL_STOCK"
#                 return f"How much initial stock for **{p['product']}**? (Enter 0 if no stock)"
        
#         elif text in ["no", "cancel", "n"]:
#             st.session_state.chat_stage = None
#             return "❌ Product addition cancelled."
    
#     # ASK INITIAL STOCK FOR NEW PRODUCT
#     if st.session_state.chat_stage == "ASK_INITIAL_STOCK":
#         stock = None
#         numbers = re.findall(r'\d+', text)
#         if numbers:
#             stock = int(numbers[0])
        
#         if stock is None:
#             return "Please enter a valid stock quantity (numbers only)"
        
#         p = st.session_state.pending_data
#         success, message = add_product_to_db(p["product"], p["price"], stock)
#         st.session_state.chat_stage = None
        
#         if success:
#             # Add the product to invoice with the requested quantity
#             action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["price"])
            
#             if action == "stock_insufficient":
#                 return f"✅ **{p['product']}** added to database at ₹{p['price']} with {stock} stock\n\n❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
#             elif action == "updated":
#                 total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                               if item['item_description'].lower() == p["product"].lower())
#                 return f"✅ **{p['product']}** added to database at ₹{p['price']} with {stock} stock\n✅ Quantity increased by {p['qty']}. Total now {total_qty}"
#             else:
#                 return f"✅ **{p['product']}** added to database at ₹{p['price']} with {stock} stock\n✅ Added {p['qty']} {p['product']} to invoice"
#         else:
#             return f"❌ {message}"
    
#     # ASK QUANTITY
#     if st.session_state.chat_stage == "ASK_QTY":
#         qty = None
#         numbers = re.findall(r'\d+', text)
#         if numbers:
#             qty = int(numbers[0])
        
#         if not qty:
#             return "Please enter a valid quantity (numbers only)"
        
#         st.session_state.pending_data["qty"] = qty
#         st.session_state.chat_stage = "ASK_PRICE"
#         return f"What should be the price for {qty} {st.session_state.pending_data['product']}?"
    
#     # ASK PRICE
#     if st.session_state.chat_stage == "ASK_PRICE":
#         price = None
#         numbers = re.findall(r'\d+(?:\.\d+)?', text)
#         if numbers:
#             price = float(numbers[0])
        
#         if not price:
#             return "Please enter a valid price (numbers only)"
        
#         p = st.session_state.pending_data
#         product = p["product"]
#         qty = p["qty"]
        
#         exists, db_price, stock = check_product_exists(product)
        
#         if not exists:
#             st.session_state.pending_data = {"product": product, "qty": qty, "price": price}
#             st.session_state.chat_stage = "ADD"
#             return f"**{product}** not found in database. Add it with price ₹{price}?"
#         else:
#             if price != db_price:
#                 st.session_state.pending_data = {
#                     "product": product,
#                     "qty": qty,
#                     "user_price": price,
#                     "db_price": db_price
#                 }
#                 st.session_state.chat_stage = "CONFIRM_PRICE_CHANGE_FOR_ORDER"
#                 return f"Database shows **{product}** price as ₹{db_price}. You entered ₹{price}. Change price?"
#             else:
#                 # Check stock availability
#                 if stock is not None and qty > stock:
#                     # Add to stock alerts
#                     st.session_state.stock_alert.append({
#                         "product": product,
#                         "requested": qty,
#                         "available": stock,
#                         "shortage": qty - stock
#                     })
#                     return f"❌ **Stock Insufficient!** Only {stock} units available for {product}"
                
#                 action, stock_info = add_or_update_invoice_item(product, qty, price)
#                 st.session_state.chat_stage = None
                
#                 if action == "stock_insufficient":
#                     return f"❌ **Stock Insufficient!** Only {stock_info} units available for {product}"
#                 elif action == "updated":
#                     total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                                   if item['item_description'].lower() == product.lower())
#                     return f"✅ Quantity increased by {qty}. Total now {total_qty} at ₹{price} each"
#                 else:
#                     return f"✅ Added {qty} {product} at ₹{price} to invoice"
    
#     # CHECK IF INVOICE SETUP IS COMPLETE BEFORE ADDING PRODUCTS
#     if not st.session_state.invoice_meta["project_id"]:
#         product, qty, price = extract_product_qty_price(user_text)
#         if product:
#             return "📋 Please start by typing 'generate invoice' to select project, party, and invoice type first."
#         else:
#             ai_response = get_ai_response(user_text, st.session_state.ai_context)
#             st.session_state.ai_context.append({"role": "assistant", "content": ai_response})
#             return ai_response
    
#     # REGULAR PRODUCT ORDER (only if setup is complete)
#     # REGULAR PRODUCT ORDER (only if setup is complete)
# 


#     if not product:
#         product = smart_product_match(user_text)

#     if not product:
#         ai_response = get_ai_response(user_text, st.session_state.ai_context)
#         st.session_state.ai_context.append({"role": "assistant", "content": ai_response})
#         return ai_response

#     # Clean product name
#     product = re.sub(r'\s*(?:rs|₹|inr|\d+)$', '', product, flags=re.IGNORECASE).strip()

#     exists, db_price, stock = check_product_exists_simple(product)

#     # Convert price to float if it exists
#     price_float = None
#     if price is not None:
#         try:
#             price_float = float(price)
#         except (ValueError, TypeError):
#             price_float = None

#     if not exists:
#         if qty is None:
#             st.session_state.chat_stage = "ASK_QTY"
#             st.session_state.pending_data = {"product": product}
#             return f"**{product}** not in database. How many?"
        
#         if price_float is None:
#             st.session_state.chat_stage = "ASK_PRICE"
#             st.session_state.pending_data = {"product": product, "qty": qty}
#             return f"Price for {qty} {product}?"
        
#         st.session_state.pending_data = {"product": product, "qty": qty, "price": price_float}
#         st.session_state.chat_stage = "ADD"
#         return f"**{product}** not in database. Add it with price ₹{price_float}?"

#     if qty is None:
#         st.session_state.chat_stage = "ASK_QTY"
#         st.session_state.pending_data = {"product": product}
#         return f"How many **{product}**? (Database price: ₹{db_price}, Stock: {stock if stock is not None else 'N/A'})"

#     if price_float is None:
#         st.session_state.chat_stage = "ASK_PRICE"
#         st.session_state.pending_data = {"product": product, "qty": qty}
#         return f"Price for {qty} {product}? (Database price: ₹{db_price}, Stock: {stock if stock is not None else 'N/A'})"

#     # Convert db_price to float for comparison
#     db_price_float = None
#     if db_price is not None:
#         try:
#             db_price_float = float(db_price)
#         except (ValueError, TypeError):
#             db_price_float = 0

#     # PRICE COMPARISON LOGIC
#     if price_float != db_price_float:
#         # Calculate price difference percentage
#         try:
#             price_diff = ((price_float - db_price_float) / db_price_float) * 100 if db_price_float > 0 else 0
#         except (ValueError, TypeError):
#             price_diff = 0
        
#         if price_float < db_price_float:
#             # Lower price - ask for confirmation
#             if price_diff < -10:  # More than 10% lower
#                 st.session_state.pending_data = {
#                     "product": product,
#                     "qty": qty,
#                     "user_price": price_float,
#                     "db_price": db_price_float,
#                     "diff_percent": abs(price_diff)
#                 }
#                 st.session_state.chat_stage = "CONFIRM_LOW_PRICE"
#                 return f"⚠️ **Warning: Lower Price!**\nDatabase price: ₹{db_price_float}\nYour price: ₹{price_float}\n({abs(price_diff):.1f}% lower)\n\nProceed with lower price?"
#             else:
#                 # Small difference, proceed automatically
#                 action, stock_info = add_or_update_invoice_item(product, qty, price_float)
                
#                 if action == "stock_insufficient":
#                     return f"❌ **Stock Insufficient!** Only {stock_info} units available for {product}"
#                 elif action == "updated":
#                     total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                                 if item['item_description'].lower() == product.lower())
#                     return f"✅ Added {qty} {product} at **slightly lower price ₹{price_float}** (DB: ₹{db_price_float}). Total now {total_qty}"
#                 else:
#                     return f"✅ Added {qty} {product} at **slightly lower price ₹{price_float}** (DB: ₹{db_price_float})"
        
#         else:  # price_float > db_price_float
#             # Higher price - ask for confirmation and option to update DB
#             st.session_state.pending_data = {
#                 "product": product,
#                 "qty": qty,
#                 "user_price": price_float,
#                 "db_price": db_price_float,
#                 "diff_percent": price_diff,
#                 "update_db": False
#             }
#             st.session_state.chat_stage = "CONFIRM_HIGH_PRICE"
#             return f"💰 **Higher Price Detected!**\nDatabase price: ₹{db_price_float}\nYour price: ₹{price_float}\n({price_diff:.1f}% higher)\n\nDo you want to:\n1. Use higher price? (Type 'yes')\n2. Use database price? (Type 'no')\n3. Update database to new price? (Type 'update')"

#     # If prices are equal or db_price_float is None, proceed with adding item
#     # Check stock before adding
#     if stock is not None and qty > stock:
#         # Add to stock alerts
#         st.session_state.stock_alert.append({
#             "product": product,
#             "requested": qty,
#             "available": stock,
#             "shortage": qty - stock
#         })
#         return f"❌ **Stock Insufficient!** Only {stock} units available for {product}"

#     action, stock_info = add_or_update_invoice_item(product, qty, price_float)

#     if action == "stock_insufficient":
#         return f"❌ **Stock Insufficient!** Only {stock_info} units available for {product}"
#     elif action == "updated":
#         total_qty = sum(item['qty'] for item in st.session_state.invoice 
#                     if item['item_description'].lower() == product.lower())
#         return f"✅ Quantity increased by {qty}. Total now {total_qty} at ₹{price_float} each"
#     else:
#         return f"✅ Added {qty} {product} at ₹{price_float} to invoice"

# # =========================
# # MAIN UI
# # =========================
# st.title("💬 CRM GST Invoice Chatbot")

# # Display stock alerts if any
# if st.session_state.stock_alert:
#     with st.expander("⚠️ Stock Alerts", expanded=True):
#         for alert in st.session_state.stock_alert:
#             st.warning(f"**{alert['product']}**: Requested {alert['requested']}, Available {alert['available']}, Shortage {alert['shortage']}")

# # Display current selection status with GST info
# if st.session_state.invoice_meta["project_name"] or st.session_state.invoice_meta["party_name"]:
#     cols = st.columns(4)
#     with cols[0]:
#         if st.session_state.invoice_meta["project_name"]:
#             st.info(f"**Project:** {st.session_state.invoice_meta['project_name']}")
#     with cols[1]:
#         if st.session_state.invoice_meta["party_name"]:
#             st.info(f"**Party:** {st.session_state.invoice_meta['party_name']}")
#     with cols[2]:
#         if st.session_state.invoice_meta["invoice_type"]:
#             st.info(f"**Type:** {st.session_state.invoice_meta['invoice_type']}")
#     with cols[3]:
#         if st.session_state.invoice_meta["party_pincode"]:
#             gst_info = get_gst_rate_from_pincode(st.session_state.invoice_meta["party_pincode"])
#             st.info(f"**GST:** {gst_info['type']}")

# # Display chat messages
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # Chat input
# if user_input := st.chat_input("Type your message here..."):
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     reply = chat_engine(user_input)
#     st.session_state.messages.append({"role": "assistant", "content": reply})
#     st.rerun()

# def show_price_comparison(product_name, user_price=None):
#     """Show price comparison between user price and database price"""
#     exists, db_price, stock = check_product_exists(product_name)
    
#     if not exists or db_price is None:
#         return None
    
#     if user_price is None:
#         return f"**Database Price:** ₹{db_price:,.2f}"
    
#     user_price = float(user_price)
#     price_diff = ((user_price - db_price) / db_price) * 100
    
#     if user_price == db_price:
#         return f"✅ **Price Match:** ₹{user_price:,.2f} (Same as database)"
    
#     elif user_price < db_price:
#         if price_diff < -10:
#             return f"⚠️ **Lower Price:** ₹{user_price:,.2f} (Database: ₹{db_price:,.2f}, {abs(price_diff):.1f}% lower)"
#         else:
#             return f"📉 **Slightly Lower:** ₹{user_price:,.2f} (Database: ₹{db_price:,.2f}, {abs(price_diff):.1f}% lower)"
    
#     else:  # user_price > db_price
#         return f"📈 **Higher Price:** ₹{user_price:,.2f} (Database: ₹{db_price:,.2f}, {price_diff:.1f}% higher)"

# # =========================
# # DISPLAY OLD INVOICE
# # =========================
# if st.session_state.viewing_old_invoice and st.session_state.old_invoice_data:
#     st.markdown("---")
#     invoice_no = st.session_state.old_invoice_data['header']['invoice_no']
#     st.subheader(f"📋 Invoice #{invoice_no}")
    
#     # Show format info if it follows new pattern
#     if invoice_no.startswith("ICE/"):
#         st.info(f"**Format:** `{invoice_no}`")
    
#     # Display invoice header info
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("Project", st.session_state.old_invoice_data['header']['project_name'])
#     with col2:
#         st.metric("Party", st.session_state.old_invoice_data['header']['party_name'])
#     with col3:
#         st.metric("Date", str(st.session_state.old_invoice_data['header']['invoice_date']))
    
#     col4, col5, col6 = st.columns(3)
#     with col4:
#         st.metric("Type", st.session_state.old_invoice_data['header']['invoice_type'])
#     with col5:
#         st.metric("Subtotal", f"₹{st.session_state.old_invoice_data['header']['subtotal']:,.2f}")
#     with col6:
#         st.metric("Grand Total", f"₹{st.session_state.old_invoice_data['header']['grand_total']:,.2f}")
    
#     # Display invoice items
#     st.subheader("📦 Invoice Items")
#     items_data = []
#     for item in st.session_state.old_invoice_data['items']:
#         items_data.append({
#             "Product": item['item_description'],
#             "Quantity": item['quantity'],
#             "Unit Price": f"₹{item['unit_price']:,.2f}",
#             "Total": f"₹{item['total_price']:,.2f}"
#         })
    
#     if items_data:
#         df_items = pd.DataFrame(items_data)
#         st.dataframe(df_items, use_container_width=True, hide_index=True)
    
#     # Display Tax breakdown
#     st.subheader("💰 Tax Calculation")
    
#     # Get tax amount from database
#     tax_amount = st.session_state.old_invoice_data['header']['tax']
#     subtotal = st.session_state.old_invoice_data['header']['subtotal']
#     grand_total = st.session_state.old_invoice_data['header']['grand_total']
    
#     # Try to calculate GST breakdown
#     if tax_amount > 0 and subtotal > 0:
#         tax_rate = (tax_amount / subtotal) * 100
        
#         col7, col8, col9 = st.columns(3)
#         if tax_rate == 18:
#             # IGST 18%
#             with col7:
#                 st.metric("IGST (18%)", f"₹{tax_amount:,.2f}")
#         elif tax_rate == 9:
#             # Single 9% tax (could be CGST or SGST)
#             with col7:
#                 st.metric("Tax (9%)", f"₹{tax_amount:,.2f}")
#         elif tax_rate == 4.5:
#             # CGST+SGST each 4.5%
#             cgst_sgst = tax_amount / 2
#             with col7:
#                 st.metric("CGST (4.5%)", f"₹{cgst_sgst:,.2f}")
#             with col8:
#                 st.metric("SGST (4.5%)", f"₹{cgst_sgst:,.2f}")
#         else:
#             # Show total tax
#             with col7:
#                 st.metric("Total Tax", f"₹{tax_amount:,.2f}")
    
#     st.divider()
#     col10, col11 = st.columns(2)
#     with col10:
#         st.metric("Total Tax", f"₹{tax_amount:,.2f}")
#     with col11:
#         st.metric("Grand Total", f"₹{grand_total:,.2f}")
    
#     # Display party info
#     if st.session_state.old_invoice_data['header']['party_address']:
#         with st.expander("📋 Party Details"):
#             st.write(f"**Address:** {st.session_state.old_invoice_data['header']['party_address']}")
#             if st.session_state.old_invoice_data['header']['party_pincode']:
#                 st.write(f"**Pincode:** {st.session_state.old_invoice_data['header']['party_pincode']}")
#             if st.session_state.old_invoice_data['header']['party_gst']:
#                 st.write(f"**GST:** {st.session_state.old_invoice_data['header']['party_gst']}")
    
#     # Clear old invoice button
#     if st.button("Close Old Invoice", type="secondary"):
#         st.session_state.viewing_old_invoice = False
#         st.session_state.old_invoice_data = None
#         st.rerun()

# # =========================
# # INVOICE VIEW WITH GST CALCULATION
# # =========================
# elif st.session_state.invoice:
#     st.markdown("---")
#     st.subheader("🧾 Current Invoice")
    
#     # Show invoice number if generated
#     if st.session_state.invoice_meta.get("invoice_no"):
#         st.success(f"**Invoice Number:** {st.session_state.invoice_meta['invoice_no']}")
    
#     # Calculate totals
#     subtotal = 0
#     for item in st.session_state.invoice:
#         qty = item.get("qty")
#         price = item.get("supply_rate")
#         if qty is not None and price is not None:
#             try:
#                 subtotal += float(qty) * float(price)
#             except (ValueError, TypeError):
#                 continue
    
#     pincode = st.session_state.invoice_meta["party_pincode"]
#     gst_calc = calculate_gst_breakdown(subtotal, pincode)
    
#     # Create dataframe with all information
#     invoice_data = []
#     for item in st.session_state.invoice:
#         row = {
#             "Product": item["item_description"],
#             "Quantity": item["qty"],
#             "Price": item["supply_rate"],
#             "Total": item["qty"] * item["supply_rate"]
#         }
        
#         # Add stock information
#         stock = get_product_stock(item["item_description"])
#         if stock is not None:
#             row["Available Stock"] = stock
#             if stock < item["qty"]:
#                 row["Stock Status"] = "⚠️ Insufficient"
#             else:
#                 row["Stock Status"] = "✅ Sufficient"
        
#         # Add meta info if available
#         if "project" in item:
#             row["Project"] = item["project"]
#         elif st.session_state.invoice_meta["project_name"]:
#             row["Project"] = st.session_state.invoice_meta["project_name"]
            
#         if "party" in item:
#             row["Party"] = item["party"]
#         elif st.session_state.invoice_meta["party_name"]:
#             row["Party"] = st.session_state.invoice_meta["party_name"]
            
#         if "invoice_type" in item:
#             row["Invoice Type"] = item["invoice_type"]
#         elif st.session_state.invoice_meta["invoice_type"]:
#             row["Invoice Type"] = st.session_state.invoice_meta["invoice_type"]
        
#         invoice_data.append(row)
    
#     df = pd.DataFrame(invoice_data)
    
#     col1, col2 = st.columns([3, 1])
    
#     with col1:
#         # Display items table with stock info
#         st.write("**Invoice Items:**")
#         edited_df = st.data_editor(
#             df,
#             use_container_width=True,
#             hide_index=True,
#             column_config={
#                 "Project": st.column_config.TextColumn("Project", disabled=True),
#                 "Party": st.column_config.TextColumn("Party", disabled=True),
#                 "Invoice Type": st.column_config.TextColumn("Type", disabled=True),
#                 "Product": st.column_config.TextColumn("Product", disabled=True),
#                 "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, disabled=False),
#                 "Price": st.column_config.NumberColumn("Price", format="₹%.2f", min_value=0.0, disabled=False),
#                 "Total": st.column_config.NumberColumn("Total", format="₹%.2f", disabled=True),
#                 "Available Stock": st.column_config.NumberColumn("Available Stock", disabled=True),
#                 "Stock Status": st.column_config.TextColumn("Stock Status", disabled=True)
#             },
#             num_rows="dynamic",
#             key="invoice_editor"
#         )
        
#         # Update if edited
#         if not df.equals(edited_df):
#             updated_invoice = []
#             for _, row in edited_df.iterrows():
#                 item = {
#                     "item_description": row["Product"],
#                     "qty": row["Quantity"],
#                     "supply_rate": row["Price"]
#                 }
                
#                 # Add back meta info
#                 if "Project" in row:
#                     item["project"] = row["Project"]
#                 if "Party" in row:
#                     item["party"] = row["Party"]
#                 if "Invoice Type" in row:
#                     item["invoice_type"] = row["Invoice Type"]
                
#                 updated_invoice.append(item)
            
#             st.session_state.invoice = updated_invoice
#             st.rerun()
    
#     with col2:
#         # Display invoice summary with new format
#         st.subheader("📋 Invoice Summary")
        
#         # Show invoice number preview if not generated yet
#         if not st.session_state.invoice_meta.get("invoice_no"):
#             # Preview what the invoice number will look like
#             invoice_type = st.session_state.invoice_meta["invoice_type"]
            
#             # Map invoice type to code
#             type_mapping = {
#                 "Credit Note": "CN",
#                 "Debit Note": "DN",
#                 "Delivery Challan": "DCH",
#                 "Purchase Invoice": "PI",
#                 "Purchase Order": "PO",
#                 "Sales Invoice": "INV",
#                 "Tax Invoice": "INV",
#                 "Proforma Invoice": "PINV"
#             }
            
#             type_code = type_mapping.get(invoice_type, "INV")
            
#             # Get current financial year
#             current_year = datetime.now().year
#             if datetime.now().month >= 4:
#                 fin_year = f"{current_year}-{current_year+1}"
#             else:
#                 fin_year = f"{current_year-1}-{current_year}"
            
#             # Try to get next sequence
#             try:
#                 with ENGINE.connect() as conn:
#                     query = text("""
#                         SELECT invoice_sequence 
#                         FROM invoice_settings 
#                         WHERE invoice_type_code = :type_code
#                         LIMIT 1
#                     """)
#                     result = conn.execute(query, {"type_code": type_code})
#                     row = result.fetchone()
#                     if row:
#                         next_seq = row[0]
#                     else:
#                         next_seq = 1
                
#                 preview_no = f"ICE/{fin_year}/{type_code}/{str(next_seq).zfill(4)}"
#                 st.info(f"**Next Invoice:**\n`{preview_no}`")
#             except:
#                 st.info(f"**Format:** ICE/{fin_year}/{type_code}/[0001+]")
        
#         st.metric("Subtotal", f"₹{subtotal:,.2f}")
        
#         if gst_calc["gst_type"] == "CGST+SGST":
#             st.metric("CGST (9%)", f"₹{gst_calc['cgst_amount']:,.2f}")
#             st.metric("SGST (9%)", f"₹{gst_calc['sgst_amount']:,.2f}")
#         else:
#             st.metric("IGST (18%)", f"₹{gst_calc['igst_amount']:,.2f}")
        
#         st.divider()
#         st.metric("Total GST", f"₹{gst_calc['total_gst']:,.2f}", 
#                   delta=f"{gst_calc['gst_type']}")
#         st.metric("Grand Total", f"₹{gst_calc['grand_total']:,.2f}", 
#                   delta_color="off")
        
#         # Display party info
#         if st.session_state.invoice_meta["party_address"]:
#             with st.expander("📋 Party Details"):
#                 st.write(f"**Address:** {st.session_state.invoice_meta['party_address']}")
#                 if st.session_state.invoice_meta["party_pincode"]:
#                     st.write(f"**Pincode:** {st.session_state.invoice_meta['party_pincode']}")
#                 if st.session_state.invoice_meta["party_gst"]:
#                     st.write(f"**GST:** {st.session_state.invoice_meta['party_gst']}")
        
#         # Stock summary
#         st.subheader("📦 Stock Summary")
#         for item in st.session_state.invoice:
#             stock = get_product_stock(item["item_description"])
#             if stock is not None:
#                 if stock >= item["qty"]:
#                     st.success(f"{item['item_description']}: {stock} → {stock - item['qty']} (after invoice)")
#                 else:
#                     st.error(f"{item['item_description']}: Only {stock} available, need {item['qty']}")
        
#         # Generate Invoice Button
#         if st.button("📤 Generate Final Invoice", type="primary", use_container_width=True):
#             success, message = save_invoice_to_db()
#             if success:
#                 st.success("✅ Invoice generated successfully!")
#                 st.info(message)
#                 # Show the generated invoice number
#                 if st.session_state.invoice_meta.get("invoice_no"):
#                     st.balloons()
#                     st.subheader(f"🎉 Invoice Generated: {st.session_state.invoice_meta['invoice_no']}")
                
#                 # Clear invoice after generation
#                 st.session_state.invoice = []
#                 st.session_state.stock_alert = []
#                 st.rerun()
#             else:
#                 st.error(f"❌ {message}")

# # Initial greeting
# if not st.session_state.messages:
#     with st.chat_message("assistant"):
#         greeting = "👋 **Hi! I'm your Invoice Assistant with GST Calculation & Stock Management**\n\n"
        
#         # Add price comparison examples
#         greeting += "**✨ Smart Price Detection:**\n"
#         greeting += "• If you say 'pen is ₹50 only' - I'll check if database price is different\n"
#         greeting += "• If you say 'pen rate is cheaper by ₹10' - I'll compare with database\n"
#         greeting += "• If you say 'old price was ₹60, new is ₹70' - I'll alert you\n\n"
        
#         # Add update commands
#         greeting += "**🔄 Update Commands:**\n"
#         greeting += "• '**update pen quantity to 10**' - Updates invoice & database\n"
#         greeting += "• '**change screwdriver price to ₹50**' - Updates invoice & database\n"
#         greeting += "• '**set hammer stock to 20**' - Updates database stock\n"
#         greeting += "• '**update notebook rate as ₹25**' - Updates price in both\n\n"
        
#         greeting += "**Examples:**\n"
#         greeting += "• 'Pen price is ₹45 only' → Checks database price\n"
#         greeting += "• 'Need 10 notebooks at ₹100 each' → Compares with DB\n"
#         greeting += "• 'Screwdriver cheaper by ₹20' → Shows difference\n"
#         greeting += "• 'Hammer more expensive now ₹500' → Alerts price increase\n"
#         greeting += "• 'Update pen quantity to 15' → Updates invoice and database\n"
#         greeting += "• 'Change screwdriver price to ₹75' → Updates price in both\n\n"
        
#         greeting += "**To create an invoice:**\n"
#         greeting += "1. Type '**generate invoice**'\n"
#         greeting += "2. Select project from database\n" 
#         greeting += "3. Select party (with address, pincode, GST from database)\n"
#         greeting += "4. Select invoice type\n"
#         greeting += "5. Add products (e.g., 'i need 10 pen for 50 rs')\n"
#         greeting += "6. Click 'Generate Final Invoice' button\n\n"
#         greeting += "**To view invoices:**\n"
#         greeting += "• Type '**list invoices**' to see all invoices\n"
#         greeting += "• Type '**view invoice ICE/25-26/INV/0018**' (with the complete invoice number)\n\n"
#         greeting += "**✨ Stock Management:**\n"
#         greeting += "• Automatically checks stock availability\n"
#         greeting += "• Updates stock after invoice generation\n"
#         greeting += "• Alerts for insufficient stock\n\n"
#         greeting += "**Stock Commands:**\n"
#         greeting += "• '**check stock pen**' - Check available stock\n"
#         greeting += "• '**add stock pen by 10**' - Increase stock\n"
#         greeting += "• '**set stock pen to 50**' - Set specific stock quantity\n\n"
#         greeting += "**Other Commands:**\n"
#         greeting += "• Change prices: '**change pen price to ₹10**'\n"
#         greeting += "• Debug: '**debug tables**', '**debug table parties**'\n"
#         greeting += "• Search: '**search invoices PO/020**'\n"
#         greeting += "• Type '**view invoice ICE/25-26/INV/0018**' (with the complete invoice number)\n\n"
#         greeting += "**New Invoice Format:**\n"
#         greeting += "• ICE/25-26/INV/0001 (Sales Invoice)\n"
#         greeting += "• ICE/25-26/PO/0001 (Purchase Order)\n"
#         greeting += "• ICE/25-26/CN/0001 (Credit Note)\n"
#         greeting += "• ICE/25-26/DN/0001 (Debit Note)\n"
#         greeting += "• ICE/25-26/DCH/0001 (Delivery Challan)\n"
#         greeting += "• ICE/25-26/PI/0001 (Purchase Invoice)\n\n"
#         greeting += "**New Invoice Format Examples:**\n"
#         greeting += "• `ICE/25-26/INV/0001` (Sales Invoice)\n"
#         greeting += "• `ICE/25-26/PO/0001` (Purchase Order)\n"
#         greeting += "• `ICE/25-26/CN/0001` (Credit Note)\n"
#         greeting += "• `ICE/25-26/DN/0001` (Debit Note)\n"
#         greeting += "• `ICE/25-26/DCH/0001` (Delivery Challan)\n"
#         greeting += "• `ICE/25-26/PI/0001` (Purchase Invoice)\n\n"
#         greeting += "**To create an invoice:**\n"
#         greeting += "**🔄 Update Commands:**\n"
#         greeting += "• '**increase pen by 5**' - Increase quantity in invoice\n"
#         greeting += "• '**delete pen row**' - Remove item from invoice\n"
#         greeting += "• '**update pen quantity to 10**' - Updates invoice & database\n"
#         greeting += "• '**change screwdriver price to ₹50**' - Updates invoice & database\n"
#         greeting += "• '**set hammer stock to 20**' - Updates database stock\n"
#         greeting += "• '**update notebook rate as ₹25**' - Updates price in both\n\n"
        
#         st.markdown(greeting)
#         st.session_state.messages.append({
#             "role": "assistant", 
#             "content": greeting
#         })






















import streamlit as st
import pandas as pd
import requests
import json
import os
import re
from dotenv import load_dotenv
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from datetime import datetime
from openai import OpenAI
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import csv
import io


# =========================
# LOAD ENV
# =========================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CRM_URL = os.getenv("CRM_URL")

DB_USER = os.getenv("DB_USER")
DB_PASS_RAW = os.getenv("DB_PASSWORD")
DB_PASS = quote_plus(DB_PASS_RAW)
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="CRM GST Invoice – WhatsApp Chatbot", layout="wide")

# =========================
# DB ENGINE
# =========================
ENGINE = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True
)

# =========================
# INITIALIZE OPENAI CLIENT
# =========================
if OPENAI_API_KEY and OPENAI_API_KEY != "skip_ai":
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

# =========================
# SESSION STATE
# =========================
defaults = {
    "messages": [],
    "chat_stage": None,
    "pending_data": {},
    "invoice": [],
    "invoice_flow": None,
    "invoice_meta": {
        "project_id": None,
        "project_name": None,
        "party_id": None,
        "party_name": None,
        "party_address": None,
        "party_pincode": None,
        "party_gst": None,
        "invoice_type": None,
        "invoice_no": None,
        "invoice_date": None,
        "total_amount": 0,
        "gst_percentage": 18,
        "cgst": 0,
        "sgst": 0,
        "igst": 0,
        "grand_total": 0,
        "invoice_prefix": None,
        "invoice_sequence": None
    },
    "awaiting_choice": False,
    "choice_type": None,
    "choice_options": [],
    "product_flow": None,
    "temp_product": {},
    "ai_context": [],
    "viewing_old_invoice": False,
    "old_invoice_data": None,
    "stock_alert": [],
    "product_suggestions": [],
    "last_product_search": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v




# =========================
# GST CALCULATION FUNCTIONS
# =========================

def get_gst_rate_from_pincode(pincode):
    """Determine GST rate based on pincode"""
    if not pincode:
        return {
            "type": "CGST+SGST",
            "cgst_rate": 9,
            "sgst_rate": 9,
            "igst_rate": 0,
            "total_gst_rate": 18
        }
    
    # Extract only digits from pincode
    pincode_str = re.sub(r'\D', '', str(pincode))
    
    # Check if we have at least 6 digits
    if len(pincode_str) >= 6:
        first_two = pincode_str[:2]
        
        # Tamil Nadu pincodes start with 60-64
        if first_two in ['60', '61', '62', '63', '64']:
            return {
                "type": "CGST+SGST",
                "cgst_rate": 9,
                "sgst_rate": 9,
                "igst_rate": 0,
                "total_gst_rate": 18
            }
    
    # Default to IGST for other states
    return {
        "type": "IGST",
        "cgst_rate": 0,
        "sgst_rate": 0,
        "igst_rate": 18,
        "total_gst_rate": 18
    }

def calculate_gst_breakdown(subtotal, pincode=None, party_state=None):
    """Calculate GST breakdown"""
    if not subtotal or subtotal <= 0:
        return {
            "subtotal": 0,
            "cgst_amount": 0,
            "sgst_amount": 0,
            "igst_amount": 0,
            "total_gst": 0,
            "grand_total": 0,
            "gst_type": "Not Calculated",
            "cgst_rate": 0,
            "sgst_rate": 0,
            "igst_rate": 0
        }
    
    gst_info = get_gst_rate_from_pincode(pincode)
    
    if gst_info["type"] == "CGST+SGST":
        cgst_amount = (subtotal * gst_info["cgst_rate"]) / 100
        sgst_amount = (subtotal * gst_info["sgst_rate"]) / 100
        igst_amount = 0
    else:
        cgst_amount = 0
        sgst_amount = 0
        igst_amount = (subtotal * gst_info["igst_rate"]) / 100
    
    total_gst = cgst_amount + sgst_amount + igst_amount
    grand_total = subtotal + total_gst
    
    return {
        "subtotal": subtotal,
        "cgst_amount": round(cgst_amount, 2),
        "sgst_amount": round(sgst_amount, 2),
        "igst_amount": round(igst_amount, 2),
        "total_gst": round(total_gst, 2),
        "grand_total": round(grand_total, 2),
        "gst_type": gst_info["type"],
        "cgst_rate": gst_info["cgst_rate"],
        "sgst_rate": gst_info["sgst_rate"],
        "igst_rate": gst_info["igst_rate"]
    }

def get_product_suggestions(search_term):
    """Get product suggestions from database based on search term"""
    if not search_term or len(search_term) < 2:
        return []
    
    try:
        with ENGINE.connect() as conn:
            query = text("""
                SELECT DISTINCT item_description 
                FROM boq_items 
                WHERE LOWER(item_description) LIKE :pattern
                ORDER BY item_description
                LIMIT 10
            """)
            result = conn.execute(query, {"pattern": f"%{search_term.lower()}%"}).fetchall()
            return [row[0] for row in result]
    except Exception as e:
        print(f"Error getting product suggestions: {e}")
        return []
    

    # =========================
    # DATABASE FUNCTIONS - STOCK MANAGEMENT
    # =========================

def get_projects():
    """Fetch all projects from database"""
    try:
        with ENGINE.connect() as conn:
            query = text("SELECT id, project_name FROM projects ORDER BY project_name")
            result = conn.execute(query)
            projects = [(row[0], row[1]) for row in result.fetchall()]
            return projects
    except Exception as e:
        return []

def get_parties():
    """Fetch all parties from database with address, pincode, GST"""
    try:
        with ENGINE.connect() as conn:
            # First get column names
            query = text("SHOW COLUMNS FROM parties")
            result = conn.execute(query)
            columns = [row[0] for row in result.fetchall()]
            
            # Build query based on available columns
            select_cols = ["id"]
            
            # Find name column
            name_cols = ["party_name", "name", "company_name", "customer_name", "vendor_name", "client_name"]
            name_col = None
            for col in name_cols:
                if col in columns:
                    select_cols.append(f"{col} as name")
                    name_col = col
                    break
            
            if not name_col:
                select_cols.append("id as name")
            
            # Add address columns if available
            address_cols = ["address", "billingAddress", "billing_address", "party_address", "street", "city"]
            for col in address_cols:
                if col in columns:
                    select_cols.append(f"{col} as address")
                    break
            
            # Add pincode if available
            pincode_cols = ["pincode", "pin_code", "postal_code", "zip_code"]
            for col in pincode_cols:
                if col in columns:
                    select_cols.append(f"{col} as pincode")
                    break
            
            # Add GST if available
            gst_cols = ["gst_number", "gst", "gstin", "gst_no"]
            for col in gst_cols:
                if col in columns:
                    select_cols.append(f"{col} as gst")
                    break
            
            # Execute query
            query = text(f"SELECT {', '.join(select_cols)} FROM parties ORDER BY name")
            result = conn.execute(query)
            
            # Process results
            parties = []
            for row in result.fetchall():
                party_data = {
                    "id": row[0],
                    "name": row[1] if len(row) > 1 and row[1] is not None else str(row[0])
                }
                
                # Add address if available
                if len(row) > 2 and row[2] is not None:
                    party_data["address"] = str(row[2]).strip()
                
                # Add pincode if available
                if len(row) > 3 and row[3] is not None:
                    pincode_val = str(row[3]).strip()
                    # Try to extract 6-digit pincode
                    pincode_match = re.search(r'(\d{6})', pincode_val)
                    if pincode_match:
                        party_data["pincode"] = pincode_match.group(1)
                    elif re.match(r'^\d{6}$', pincode_val):
                        party_data["pincode"] = pincode_val
                
                # Add GST if available
                if len(row) > 4 and row[4] is not None:
                    party_data["gst"] = str(row[4]).strip()
                
                # If pincode is missing but address has a pincode, extract it
                if "pincode" not in party_data and "address" in party_data:
                    address = party_data["address"]
                    # Look for 6-digit number in the address (usually at the end)
                    pincode_match = re.search(r'(\d{6})', address)
                    if pincode_match:
                        party_data["pincode"] = pincode_match.group(1)
                
                parties.append(party_data)
            
            return parties
    except Exception as e:
        print(f"Error in get_parties: {e}")
        return []

def get_invoice_types():
    """Get invoice types from database with mappings"""
    try:
        with ENGINE.connect() as conn:
            query = text("SHOW COLUMNS FROM invoices LIKE 'type'")
            result = conn.execute(query)
            if result.fetchone():
                query = text("SELECT DISTINCT type FROM invoices WHERE type IS NOT NULL AND type != '' ORDER BY type")
                result = conn.execute(query)
                types = [row[0] for row in result.fetchall()]
                if types:
                    # Add codes to existing types based on your database values
                    type_with_codes = []
                    for t in types:
                        code = get_type_code(t)
                        type_with_codes.append(f"{t} ({code})")
                    return type_with_codes
        
        # Fallback to default types with codes
        return [
            "sales (INV)",
            "purchase (PI)", 
            "purchase_order (PO)",
            "credit (CN)",
            "debit (DN)",
            "delivery_challan (DCH)"
        ]
    except Exception as e:
        # Return your database types as default
        return [
            "sales (INV)",
            "purchase (PI)", 
            "purchase_order (PO)",
            "credit (CN)",
            "debit (DN)",
            "delivery_challan (DCH)"
        ]

def get_type_code(invoice_type):
    """Get code for invoice type"""
    # Clean the invoice type - remove any parentheses and trim
    clean_type = invoice_type.strip().lower()
    
    # First, handle the exact types from your database
    if clean_type == "purchase":
        return "PI"
    elif clean_type == "purchase_order":
        return "PO"
    elif clean_type == "sales":
        return "INV"
    elif clean_type == "credit":
        return "CN"
    elif clean_type == "debit":
        return "DN"
    elif clean_type == "delivery_challan":
        return "DCH"
    
    # Then handle other variations
    type_mapping = {
        "credit": "CN",
        "debit": "DN", 
        "delivery challan": "DCH",
        "delivery_challan": "DCH",
        "purchase": "PI",
        "purchase invoice": "PI",
        "purchase order": "PO",
        "purchase_order": "PO",
        "sales": "INV",
        "sales invoice": "INV",
        "tax invoice": "INV",
        "proforma invoice": "PINV",
        "credit note": "CN",
        "debit note": "DN", 
        "delivery challan (dch)": "DCH",
        "purchase invoice (pi)": "PI",
        "purchase order (po)": "PO",
        "sales invoice (inv)": "INV",
        "tax invoice (inv)": "INV",
        "proforma invoice (pınv)": "PINV"
    }
    
    # Try exact match first
    if clean_type in type_mapping:
        return type_mapping[clean_type]
    
    # Try partial match
    for key in type_mapping:
        if key in clean_type or clean_type in key:
            return type_mapping[key]
    
    # Default
    return "INV"

def get_product_id(product_name):
    """Get product ID from boq_items table"""
    try:
        with ENGINE.connect() as conn:
            query = text("SELECT id FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
            result = conn.execute(query, {"p": product_name})
            row = result.fetchone()
            if row:
                return row[0]
            return None
    except Exception as e:
        print(f"Error getting product ID for {product_name}: {e}")
        return None

def get_product_options():
    """Fetch all products from database"""
    try:
        with ENGINE.connect() as conn:
            query = text("SELECT DISTINCT item_description FROM boq_items ORDER BY item_description")
            result = conn.execute(query)
            products = [row[0] for row in result.fetchall()]
            return products
    except Exception as e:
        return []

def get_product_stock(product_name):
    """Get available stock quantity for a product from boq_items table"""
    try:
        with ENGINE.connect() as conn:
            query = text("""
                SELECT quantity 
                FROM boq_items 
                WHERE LOWER(item_description) = LOWER(:p)
            """)
            result = conn.execute(query, {"p": product_name})
            row = result.fetchone()
            if row:
                return float(row[0])
            return None
    except Exception as e:
        print(f"Error getting stock for {product_name}: {e}")
        return None

def check_product_exists(product_name):
    """Check if product exists in database and return id, price, stock"""
    try:
        with ENGINE.connect() as conn:
            query = text("SELECT id, supply_rate, quantity FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
            result = conn.execute(query, {"p": product_name})
            row = result.fetchone()
            if row:
                # Convert to appropriate types
                product_id = int(row[0]) if row[0] is not None else None
                price = float(row[1]) if row[1] is not None else None
                stock = float(row[2]) if row[2] is not None else None
                return True, product_id, price, stock
            return False, None, None, None
    except Exception as e:
        print(f"Error checking product: {e}")
        return False, None, None, None

def check_product_exists_simple(product_name):
    """Simple version - returns (exists, price, stock) for backward compatibility"""
    try:
        with ENGINE.connect() as conn:
            query = text("SELECT supply_rate, quantity FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
            result = conn.execute(query, {"p": product_name})
            row = result.fetchone()
            if row:
                price = float(row[0]) if row[0] is not None else None
                stock = float(row[1]) if row[1] is not None else None
                return True, price, stock
            return False, None, None
    except Exception as e:
        print(f"Error checking product (simple): {e}")
        return False, None, None

def add_product_to_db(product_name, price, initial_stock=0):
    """Add new product to database"""
    try:
        with ENGINE.begin() as conn:
            query = text("""
                INSERT INTO boq_items 
                (project_id, item_description, quantity, unit, supply_rate, created_by)
                VALUES (1, :p, :qty, 'nos', :r, 1)
            """)
            conn.execute(query, {"p": product_name, "r": price, "qty": initial_stock})
        return True, "Product added successfully"
    except Exception as e:
        return False, f"Error adding product: {str(e)}"

def update_product_price(product_name, new_price):
    """Update product price in database"""
    try:
        with ENGINE.begin() as conn:
            query = text("""
                UPDATE boq_items 
                SET supply_rate = :r 
                WHERE LOWER(item_description) = LOWER(:p)
            """)
            conn.execute(query, {"p": product_name, "r": new_price})
        return True, "Price updated successfully"
    except Exception as e:
        return False, f"Error updating price: {str(e)}"

def remove_product_from_invoice(product_name):
    """Remove product from current invoice"""
    product_lower = product_name.lower()
    removed = False
    original_length = len(st.session_state.invoice)
    
    # Filter out the product to be removed
    new_invoice = []
    for item in st.session_state.invoice:
        if item["item_description"].lower() != product_lower:
            new_invoice.append(item)
        else:
            removed = True
    
    # Update the invoice
    st.session_state.invoice = new_invoice
    
    if removed:
        return True, f"✅ Removed '{product_name}' from invoice"
    else:
        return False, f"❌ '{product_name}' not found in current invoice"

def update_product_stock(product_name, new_stock):
    """Update product stock quantity in database"""
    try:
        with ENGINE.begin() as conn:
            query = text("""
                UPDATE boq_items 
                SET quantity = :qty 
                WHERE LOWER(item_description) = LOWER(:p)
            """)
            conn.execute(query, {"p": product_name, "qty": new_stock})
        return True, "Stock updated successfully"
    except Exception as e:
        return False, f"Error updating stock: {str(e)}"

def increase_product_stock(product_name, additional_stock):
    """Increase product stock quantity"""
    try:
        current_stock = get_product_stock(product_name)
        if current_stock is None:
            return False, "Product not found"
        
        new_stock = current_stock + additional_stock
        success, message = update_product_stock(product_name, new_stock)
        if success:
            return True, f"✅ Stock increased by {additional_stock}. New stock: {new_stock}"
        return False, message
    except Exception as e:
        return False, f"Error increasing stock: {str(e)}"

def decrease_product_stock(product_name, quantity_to_decrease):
    """Decrease product stock quantity after invoice generation"""
    try:
        current_stock = get_product_stock(product_name)
        if current_stock is None:
            return False, "Product not found"
        
        if current_stock < quantity_to_decrease:
            return False, f"Insufficient stock. Available: {current_stock}, Required: {quantity_to_decrease}"
        
        new_stock = current_stock - quantity_to_decrease
        success, message = update_product_stock(product_name, new_stock)
        if success:
            return True, f"✅ Stock decreased by {quantity_to_decrease}. Remaining stock: {new_stock}"
        return False, message
    except Exception as e:
        return False, f"Error decreasing stock: {str(e)}"

def get_next_invoice_number():
    """Get next invoice number using format: ICE/2025-2026/[TYPE]/[SEQUENCE]"""
    try:
        with ENGINE.connect() as conn:
            # Get invoice type from session state
            invoice_type = st.session_state.invoice_meta.get("invoice_type", "sales")
            
            # Get type code using the mapping function
            type_code = get_type_code(invoice_type)
            
            # Get current financial year (assuming Apr-Mar) - use 4-digit year
            current_year = datetime.now().year
            if datetime.now().month >= 4:
                fin_year = f"{current_year}-{current_year+1}"
            else:
                fin_year = f"{current_year-1}-{current_year}"
            
            print(f"Generating invoice number for type: '{invoice_type}' -> code: '{type_code}'")
            
            # First, try to get sequence from invoice_settings table
            query = text("SHOW TABLES LIKE 'invoice_settings'")
            result = conn.execute(query)
            
            if result.fetchone():
                # Get the current sequence for this type
                query = text("""
                    SELECT invoice_prefix, invoice_sequence, invoice_type_code 
                    FROM invoice_settings 
                    WHERE invoice_type_code = :type_code
                    LIMIT 1
                """)
                result = conn.execute(query, {"type_code": type_code})
                row = result.fetchone()
                
                if row:
                    prefix = row[0] or "ICE"
                    sequence = row[1] or 1
                    
                    # Update sequence for next invoice
                    update_query = text("""
                        UPDATE invoice_settings 
                        SET invoice_sequence = :seq + 1 
                        WHERE invoice_type_code = :type_code
                    """)
                    conn.execute(update_query, {"seq": sequence, "type_code": type_code})
                    conn.commit()
                    
                    invoice_number = f"{prefix}/{fin_year}/{type_code}/{str(sequence).zfill(4)}"
                    print(f"Generated from invoice_settings: {invoice_number}")
                    return invoice_number, prefix, sequence, type_code
                
                # If no record for this type, create one
                else:
                    # Start sequence from 1 for new type
                    sequence = 1
                    
                    # Insert new record for this type
                    insert_query = text("""
                        INSERT INTO invoice_settings 
                        (invoice_prefix, invoice_sequence, invoice_type_code, created_at)
                        VALUES (:prefix, :seq, :type_code, NOW())
                    """)
                    conn.execute(insert_query, {
                        "prefix": "ICE",
                        "seq": sequence,
                        "type_code": type_code
                    })
                    conn.commit()
                    
                    invoice_number = f"ICE/{fin_year}/{type_code}/{str(sequence).zfill(4)}"
                    print(f"Created new record in invoice_settings: {invoice_number}")
                    return invoice_number, "ICE", sequence, type_code
            
            # Fallback: Check invoices table for last sequence of this type
            else:
                # Try different patterns
                patterns = [
                    f"%ICE/{fin_year}/{type_code}/%",
                    f"%{fin_year}/{type_code}/%",
                    f"%/{type_code}/%"
                ]
                
                last_sequence = 0
                for pattern in patterns:
                    query = text("""
                        SELECT invoiceNumber, invoice_number_generated 
                        FROM invoices 
                        WHERE invoiceNumber LIKE :pattern OR invoice_number_generated LIKE :pattern
                        ORDER BY createdAt DESC 
                        LIMIT 1
                    """)
                    result = conn.execute(query, {"pattern": pattern})
                    row = result.fetchone()
                    
                    if row:
                        # Extract the last sequence number
                        invoice_str = row[0] or row[1] or ""
                        match = re.search(r'/(\d{4})$', invoice_str)
                        if match:
                            last_seq = int(match.group(1))
                            last_sequence = max(last_sequence, last_seq)
                
                sequence = last_sequence + 1 if last_sequence > 0 else 1
                invoice_number = f"ICE/{fin_year}/{type_code}/{str(sequence).zfill(4)}"
                print(f"Generated from invoices table: {invoice_number}")
                return invoice_number, "ICE", sequence, type_code
                
    except Exception as e:
        print(f"Error in get_next_invoice_number: {e}")
        # Fallback format
        current_year = datetime.now().year
        if datetime.now().month >= 4:
            fin_year = f"{current_year}-{current_year+1}"
        else:
            fin_year = f"{current_year-1}-{current_year}"
        
        # Get type code
        invoice_type = st.session_state.invoice_meta.get("invoice_type", "sales")
        type_code = get_type_code(invoice_type)
        
        fallback_number = f"ICE/{fin_year}/{type_code}/0001"
        print(f"Using fallback: {fallback_number}")
        return fallback_number, "ICE", 1, type_code
        
        # # In the chat engine function, add this debug command
        # if text == "debug type mapping":
        #     invoice_type = st.session_state.invoice_meta.get("invoice_type")
        #     type_code = get_type_code(invoice_type)
            
        #     response = f"🔍 **Type Mapping Debug:**\n\n"
        #     response += f"**Current invoice_type in session:** '{invoice_type}'\n"
        #     response += f"**Mapped type_code:** '{type_code}'\n\n"
        #     response += "**Available mappings:**\n"
        #     response += "• 'Purchase Order' → 'PO'\n"
        #     response += "• 'Sales Invoice' → 'INV'\n"
        #     response += "• 'Purchase Invoice' → 'PI'\n"
        #     response += "• 'Credit Note' → 'CN'\n"
        #     response += "• 'Debit Note' → 'DN'\n"
        #     response += "• 'Delivery Challan' → 'DCH'\n"
        #     response += "• 'Proforma Invoice' → 'PINV'\n"
            
        #     return response
        
        # return f"ICE/{fin_year}/{type_code}/0001", "ICE", 1, type_code

def debug_database_tables():
    """Debug all database tables"""
    try:
        with ENGINE.connect() as conn:
            # Get all tables
            query = text("SHOW TABLES")
            result = conn.execute(query)
            tables = [row[0] for row in result.fetchall()]
            
            return tables
    except Exception as e:
        return f"Error: {e}"
    

def debug_all_invoice_numbers():
    """Debug function to see all invoice numbers in database"""
    try:
        with ENGINE.connect() as conn:
            query = text("""
                SELECT 
                    id,
                    invoiceNumber,
                    invoice_number_generated,
                    type,
                    date,
                    total,
                    status,
                    createdAt
                FROM invoices 
                ORDER BY createdAt DESC
                LIMIT 20
            """)
            result = conn.execute(query)
            
            invoices = []
            for row in result.fetchall():
                invoices.append({
                    "id": row[0],
                    "invoiceNumber": row[1],
                    "invoice_number_generated": row[2],
                    "type": row[3],
                    "date": row[4],
                    "total": row[5],
                    "status": row[6],
                    "createdAt": row[7]
                })
            
            return invoices
    except Exception as e:
        return f"Error: {e}"    

def debug_table_structure(table_name):
    """Debug table structure"""
    try:
        with ENGINE.connect() as conn:
            # Get all columns
            query = text(f"SHOW COLUMNS FROM {table_name}")
            result = conn.execute(query)
            columns = []
            for row in result.fetchall():
                columns.append({
                    "field": row[0],
                    "type": row[1],
                    "null": row[2],
                    "key": row[3],
                    "default": row[4],
                    "extra": row[5]
                })
            
            # Get sample data
            query = text(f"SELECT * FROM {table_name} LIMIT 3")
            result = conn.execute(query)
            sample_data = result.fetchall()
            
            return {
                "columns": columns,
                "sample_data": sample_data
            }
    except Exception as e:
        return f"Error: {e}"

def debug_search_invoices(search_term=""):
    """Debug: Search for invoices in database"""
    try:
        with ENGINE.connect() as conn:
            query = text("""
                SELECT 
                    invoice_number_generated, 
                    invoiceNumber,
                    UPPER(invoice_number_generated) as upper_gen,
                    UPPER(invoiceNumber) as upper_num,
                    date, type, total, project_id, clientId
                FROM invoices 
                WHERE invoice_number_generated IS NOT NULL OR invoiceNumber IS NOT NULL
                ORDER BY createdAt DESC 
                LIMIT 20
            """)
            result = conn.execute(query)
            
            invoices = []
            for row in result.fetchall():
                invoices.append({
                    "invoice_number_generated": row[0],
                    "invoiceNumber": row[1],
                    "upper_generated": row[2],
                    "upper_number": row[3],
                    "date": row[4],
                    "type": row[5],
                    "total": row[6],
                    "project_id": row[7],
                    "clientId": row[8]
                })
            
            return invoices
    except Exception as e:
        return f"Error: {e}"

def debug_invoice_items_table():
    """Debug the invoice_items table structure"""
    try:
        with ENGINE.connect() as conn:
            # Check if table exists
            query = text("SHOW TABLES LIKE 'invoice_items'")
            result = conn.execute(query)
            if not result.fetchone():
                return "❌ invoice_items table does not exist"
            
            # Get table structure
            query = text("SHOW COLUMNS FROM invoice_items")
            result = conn.execute(query)
            columns = []
            for row in result.fetchall():
                columns.append({
                    "field": row[0],
                    "type": row[1],
                    "null": row[2],
                    "key": row[3],
                    "default": row[4],
                    "extra": row[5]
                })
            
            # Get sample data
            query = text("SELECT * FROM invoice_items LIMIT 3")
            result = conn.execute(query)
            sample_data = result.fetchall()
            
            return {
                "columns": columns,
                "sample_data": sample_data
            }
    except Exception as e:
        return f"Error: {e}"

    # Add this debug command to the chat engine
    # In the chat engine function, add:
    if text == "debug invoice items":
        debug_info = debug_invoice_items_table()
        if isinstance(debug_info, str):
            return debug_info
        
        response = "🔍 **invoice_items Table Structure:**\n\n"
        response += "**Columns:**\n"
        for col in debug_info["columns"]:
            response += f"• {col['field']} ({col['type']}) - Null: {col['null']}\n"
        
        response += "\n**Sample Data (first 3 rows):**\n"
        for i, row in enumerate(debug_info["sample_data"], 1):
            response += f"{i}. {row}\n"
        
        return response

def get_invoice_by_number(invoice_no):
    """Get invoice details by invoice number - searches in invoiceNumber column"""
    try:
        with ENGINE.connect() as conn:
            # Clean the input
            clean_invoice_no = str(invoice_no).strip()
            
            print(f"Searching for invoice: '{clean_invoice_no}'")  # Debug
            
            # Strategy 1: Search in invoiceNumber column (exact match)
            query = text("""
                SELECT 
                    id, invoiceNumber, project_id, clientId, type, date,
                    subTotal, tax, discount, total, 
                    notes, meta, invoice_prefix, invoice_sequence,
                    status, createdAt, updatedAt
                FROM invoices 
                WHERE invoiceNumber = :no
                ORDER BY createdAt DESC
                LIMIT 1
            """)
            result = conn.execute(query, {"no": clean_invoice_no})
            header = result.fetchone()
            
            # Strategy 2: Try in invoice_number_generated column
            if not header:
                query = text("""
                    SELECT 
                        id, invoice_number_generated, project_id, clientId, type, date,
                        subTotal, tax, discount, total, 
                        notes, meta, invoice_prefix, invoice_sequence,
                        status, createdAt, updatedAt, invoice_type_code
                    FROM invoices 
                    WHERE invoice_number_generated = :no
                    ORDER BY createdAt DESC
                    LIMIT 1
                """)
                result = conn.execute(query, {"no": clean_invoice_no})
                header = result.fetchone()
                
                if header:
                    # Convert to match expected structure
                    header = list(header)
                    # Keep invoice_number_generated as invoiceNumber for consistency
                    invoice_number = header[1]
                    header = header[:1] + [invoice_number] + header[2:]
            
            # Strategy 3: Case-insensitive search in invoiceNumber
            if not header:
                query = text("""
                    SELECT 
                        id, invoiceNumber, project_id, clientId, type, date,
                        subTotal, tax, discount, total, 
                        notes, meta, invoice_prefix, invoice_sequence,
                        status, createdAt, updatedAt
                    FROM invoices 
                    WHERE UPPER(invoiceNumber) = UPPER(:no)
                    ORDER BY createdAt DESC
                    LIMIT 1
                """)
                result = conn.execute(query, {"no": clean_invoice_no})
                header = result.fetchone()
            
            # Strategy 4: Try without any special formatting
            if not header:
                # Remove all spaces and try
                clean_no_no_spaces = clean_invoice_no.replace(" ", "")
                query = text("""
                    SELECT 
                        id, invoiceNumber, project_id, clientId, type, date,
                        subTotal, tax, discount, total, 
                        notes, meta, invoice_prefix, invoice_sequence,
                        status, createdAt, updatedAt
                    FROM invoices 
                    WHERE REPLACE(invoiceNumber, ' ', '') = :no
                    ORDER BY createdAt DESC
                    LIMIT 1
                """)
                result = conn.execute(query, {"no": clean_no_no_spaces})
                header = result.fetchone()
            
            # Strategy 5: Partial match search
            if not header:
                # Try with different patterns
                patterns = [
                    f"%{clean_invoice_no}%",
                    f"%{clean_invoice_no.replace('/', '/')}%",
                    f"%{clean_invoice_no.replace('ICE/', '')}%",
                    f"%INV/{clean_invoice_no.split('/')[-1] if '/' in clean_invoice_no else clean_invoice_no}%"
                ]
                
                for pattern in patterns:
                    query = text("""
                        SELECT 
                            id, invoiceNumber, project_id, clientId, type, date,
                            subTotal, tax, discount, total, 
                            notes, meta, invoice_prefix, invoice_sequence,
                            status, createdAt, updatedAt
                        FROM invoices 
                        WHERE invoiceNumber LIKE :pattern
                        ORDER BY createdAt DESC
                        LIMIT 1
                    """)
                    result = conn.execute(query, {"pattern": pattern})
                    header = result.fetchone()
                    if header:
                        break
            
            # Strategy 6: Search by sequence number only
            if not header:
                # Extract just the numeric part (last 4 digits)
                match = re.search(r'(\d{4})$', clean_invoice_no)
                if match:
                    seq_num = match.group(1)
                    query = text("""
                        SELECT 
                            id, invoiceNumber, project_id, clientId, type, date,
                            subTotal, tax, discount, total, 
                            notes, meta, invoice_prefix, invoice_sequence,
                            status, createdAt, updatedAt
                        FROM invoices 
                        WHERE invoiceNumber LIKE :pattern
                        ORDER BY createdAt DESC
                        LIMIT 1
                    """)
                    result = conn.execute(query, {"pattern": f"%/{seq_num}"})
                    header = result.fetchone()
            
            if header:
                invoice_id = header[0]  # Get the invoice ID
                invoice_number = header[1]
                print(f"Found invoice: {invoice_number}, ID: {invoice_id}")
                
                # Get project name
                project_name = "Unknown"
                try:
                    query = text("SELECT project_name FROM projects WHERE id = :id")
                    result = conn.execute(query, {"id": header[2]})
                    project_row = result.fetchone()
                    if project_row:
                        project_name = project_row[0]
                except Exception as e:
                    print(f"Error getting project name: {e}")
                
                # Get party/client name
                party_name = "Unknown"
                party_address = None
                party_pincode = None
                party_gst = None
                
                try:
                    # First check what columns exist in parties table
                    query = text("SHOW COLUMNS FROM parties")
                    result = conn.execute(query)
                    columns = [row[0] for row in result.fetchall()]
                    
                    # Determine the name column
                    name_column = None
                    possible_name_columns = ['party_name', 'name', 'company_name', 'customer_name', 'vendor_name', 'client_name']
                    
                    for col in possible_name_columns:
                        if col in columns:
                            name_column = col
                            break
                    
                    if not name_column and columns:
                        for col in columns:
                            if col not in ['id', 'createdAt', 'updatedAt', 'status']:
                                name_column = col
                                break
                    
                    # Build query to get party info
                    if name_column:
                        select_parts = [f"{name_column} as party_name"]
                        
                        # Check for address column
                        address_columns = ['address', 'billingAddress', 'billing_address', 'party_address', 'street', 'city']
                        for col in address_columns:
                            if col in columns:
                                select_parts.append(f"{col} as address")
                                break
                        
                        # Check for pincode column
                        pincode_columns = ['pincode', 'pin_code', 'postal_code', 'zip_code']
                        for col in pincode_columns:
                            if col in columns:
                                select_parts.append(f"{col} as pincode")
                                break
                        
                        # Check for GST column
                        gst_columns = ['gst_number', 'gst', 'gstin', 'gst_no']
                        for col in gst_columns:
                            if col in columns:
                                select_parts.append(f"{col} as gst")
                                break
                        
                        query_str = f"SELECT {', '.join(select_parts)} FROM parties WHERE id = :id"
                        query = text(query_str)
                        result = conn.execute(query, {"id": header[3]})
                        party_row = result.fetchone()
                        
                        if party_row:
                            party_name = party_row[0] if party_row[0] else "Unknown"
                            if len(party_row) > 1:
                                party_address = party_row[1]
                            if len(party_row) > 2:
                                party_pincode = party_row[2]
                            if len(party_row) > 3:
                                party_gst = party_row[3]
                except Exception as e:
                    print(f"Error getting party info: {e}")
                
                # Get invoice items from invoice_items table using invoiceId
                items = []
                try:
                    query = text("""
                        SELECT 
                            description, uom, quantity, rate, discount, 
                            tax, taxAmount, amount
                        FROM invoice_items 
                        WHERE invoiceId = :invoice_id
                        ORDER BY id
                    """)
                    result = conn.execute(query, {"invoice_id": invoice_id})
                    db_items = result.fetchall()
                    
                    if db_items:
                        for item in db_items:
                            items.append({
                                "item_description": item[0] or "",  # description
                                "uom": item[1] or "",  # uom
                                "quantity": float(item[2]) if item[2] else 0,  # quantity
                                "unit_price": float(item[3]) if item[3] else 0,  # rate
                                "discount": float(item[4]) if item[4] else 0,  # discount
                                "tax_percentage": float(item[5]) if item[5] else 0,  # tax percentage
                                "tax_amount": float(item[6]) if item[6] else 0,  # tax amount
                                "total_price": float(item[7]) if item[7] else 0  # amount
                            })
                    else:
                        print(f"No items found in invoice_items for invoiceId: {invoice_id}")
                        
                        # Fallback: Try from notes JSON
                        if header[9]:  # notes column
                            try:
                                notes_data = json.loads(header[9])
                                if isinstance(notes_data, dict):
                                    # Check different possible structures
                                    if 'items' in notes_data:
                                        for item in notes_data['items']:
                                            items.append({
                                                "item_description": item.get('description', '') or item.get('item_description', ''),
                                                "uom": item.get('uom', ''),
                                                "quantity": float(item.get('quantity', 0)),
                                                "unit_price": float(item.get('unit_price', 0) or item.get('rate', 0) or item.get('price', 0)),
                                                "discount": float(item.get('discount', 0)),
                                                "tax_percentage": float(item.get('tax', 0)),
                                                "tax_amount": float(item.get('taxAmount', 0)),
                                                "total_price": float(item.get('total', 0) or item.get('amount', 0))
                                            })
                                    elif 'line_items' in notes_data:
                                        for item in notes_data['line_items']:
                                            items.append({
                                                "item_description": item.get('description', '') or item.get('item_description', ''),
                                                "uom": item.get('uom', ''),
                                                "quantity": float(item.get('quantity', 0)),
                                                "unit_price": float(item.get('unit_price', 0) or item.get('rate', 0) or item.get('price', 0)),
                                                "discount": float(item.get('discount', 0)),
                                                "tax_percentage": float(item.get('tax', 0)),
                                                "tax_amount": float(item.get('taxAmount', 0)),
                                                "total_price": float(item.get('total', 0) or item.get('amount', 0))
                                            })
                            except Exception as e:
                                print(f"Error parsing notes JSON: {e}")
                except Exception as e:
                    print(f"Error getting invoice items: {e}")
                
                # Format invoice data
                invoice_data = {
                    "header": {
                        "invoice_id": invoice_id,
                        "invoice_no": invoice_number,
                        "project_id": header[2],
                        "project_name": project_name,
                        "party_id": header[3],
                        "party_name": party_name,
                        "invoice_type": header[4],
                        "invoice_date": header[5],
                        "subtotal": float(header[6]) if header[6] else 0,
                        "tax": float(header[7]) if header[7] else 0,
                        "discount": float(header[8]) if header[8] else 0,
                        "grand_total": float(header[9]) if header[9] else 0,
                        "notes": header[10],
                        "meta": header[11],
                        "invoice_prefix": header[12],
                        "invoice_sequence": header[13],
                        "status": header[14],
                        "created_at": header[15],
                        "updated_at": header[16],
                        "party_address": party_address,
                        "party_pincode": party_pincode,
                        "party_gst": party_gst
                    },
                    "items": items
                }
                
                return invoice_data
            
            return None
    except Exception as e:
        print(f"Error in get_invoice_by_number: {e}")
        return None

def get_all_invoices():
    """Get list of all invoices from database with complete information"""
    try:
        with ENGINE.connect() as conn:
            # First get column names to check what exists
            query = text("SHOW COLUMNS FROM invoices")
            result = conn.execute(query)
            columns = [row[0] for row in result.fetchall()]
            
            # Build select query based on available columns
            select_parts = []
            
            # Essential columns
            essential_cols = [
                ("invoiceNumber", "invoice_no"),
                ("date", "invoice_date"),
                ("project_id", "project_id"),
                ("clientId", "party_id"),
                ("type", "invoice_type"),
                ("total", "grand_total"),
                ("status", "status"),
                ("createdAt", "created_at"),
                ("updatedAt", "updated_at"),
                ("notes", "notes")
            ]
            
            for db_col, alias in essential_cols:
                if db_col in columns:
                    select_parts.append(f"{db_col} as {alias}")
            
            # Add additional columns if they exist
            additional_cols = [
                ("invoice_number_generated", "invoice_generated"),
                ("invoice_prefix", "invoice_prefix"),
                ("invoice_sequence", "invoice_sequence"),
                ("subTotal", "subtotal"),
                ("tax", "tax_amount"),
                ("discount", "discount"),
                ("meta", "meta")
            ]
            
            for db_col, alias in additional_cols:
                if db_col in columns:
                    select_parts.append(f"{db_col} as {alias}")
            
            # Build and execute query
            select_query = ", ".join(select_parts)
            query = text(f"""
                SELECT {select_query}
                FROM invoices 
                WHERE (invoiceNumber IS NOT NULL AND invoiceNumber != '')
                    OR (invoice_number_generated IS NOT NULL AND invoice_number_generated != '')
                ORDER BY createdAt DESC 
                LIMIT 100
            """)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            invoices = []
            for row in rows:
                invoice = {}
                
                # Map row data to dictionary
                for i, (_, alias) in enumerate(essential_cols):
                    if i < len(row):
                        invoice[alias] = row[i]
                
                # Add additional data
                offset = len(essential_cols)
                for j, (_, alias) in enumerate(additional_cols):
                    if offset + j < len(row):
                        invoice[alias] = row[offset + j]
                
                # Get project name
                project_name = "N/A"
                if invoice.get('project_id'):
                    try:
                        query = text("SELECT project_name FROM projects WHERE id = :id")
                        project_result = conn.execute(query, {"id": invoice['project_id']})
                        project_row = project_result.fetchone()
                        if project_row:
                            project_name = project_row[0]
                    except:
                        project_name = "N/A"
                invoice['project_name'] = project_name
                
                # Get party/client name
                party_name = "N/A"
                if invoice.get('party_id'):
                    try:
                        # Check what name column exists
                        query = text("SHOW COLUMNS FROM parties")
                        result = conn.execute(query)
                        party_columns = [r[0] for r in result.fetchall()]
                        
                        name_col = None
                        for col in ['party_name', 'name', 'company_name', 'customer_name', 'vendor_name', 'client_name']:
                            if col in party_columns:
                                name_col = col
                                break
                        
                        if name_col:
                            query = text(f"SELECT {name_col} FROM parties WHERE id = :id")
                            party_result = conn.execute(query, {"id": invoice['party_id']})
                            party_row = party_result.fetchone()
                            if party_row:
                                party_name = party_row[0]
                    except:
                        party_name = "N/A"
                invoice['party_name'] = party_name
                
                # Format date and time
                if invoice.get('created_at'):
                    created_date = invoice['created_at']
                    if isinstance(created_date, datetime):
                        invoice['created_date'] = created_date.strftime("%d-%m-%Y")
                        invoice['created_time'] = created_date.strftime("%H:%M:%S")
                        invoice['datetime_display'] = f"{created_date.strftime('%d-%m-%Y %H:%M:%S')}"
                    else:
                        try:
                            # Try to parse string date
                            dt = datetime.strptime(str(created_date), "%Y-%m-%d %H:%M:%S")
                            invoice['created_date'] = dt.strftime("%d-%m-%Y")
                            invoice['created_time'] = dt.strftime("%H:%M:%S")
                            invoice['datetime_display'] = f"{dt.strftime('%d-%m-%Y %H:%M:%S')}"
                        except:
                            invoice['datetime_display'] = str(created_date)
                else:
                    invoice['datetime_display'] = "N/A"
                
                invoices.append(invoice)
            
            return invoices
    except Exception as e:
        print(f"Error in get_all_invoices: {e}")
        return []
    
def save_invoice_to_db():
    """Save invoice to database with all information including GST and update stock"""
    try:
        if not st.session_state.invoice:
            return False, "No items in invoice"
        
        if not st.session_state.invoice_meta["project_id"]:
            return False, "Project not selected"
        
        if not st.session_state.invoice_meta["party_id"]:
            return False, "Party not selected"
        
        if not st.session_state.invoice_meta["invoice_type"]:
            return False, "Invoice type not selected"
        
        # Validate and calculate subtotal with error handling
        subtotal = 0
        valid_items = []
        
        for item in st.session_state.invoice:
            # Check if values exist and are valid
            qty = item.get("qty")
            price = item.get("supply_rate")
            uom = item.get("uom", "nos")  # Get UOM or default to "nos"
            
            # Skip invalid items
            if qty is None or price is None:
                continue
                
            # Convert to float if needed
            try:
                qty = float(qty)
                price = float(price)
                
                # Ensure positive values
                if qty <= 0 or price <= 0:
                    continue
                    
                subtotal += qty * price
                valid_items.append(item)
                
            except (ValueError, TypeError):
                continue
        
        if not valid_items:
            return False, "No valid items with quantity and price in invoice"
        
        # Update invoice with only valid items
        st.session_state.invoice = valid_items
        
        pincode = st.session_state.invoice_meta["party_pincode"]
        gst_calc = calculate_gst_breakdown(subtotal, pincode)
        
        # Get invoice number with new format
        invoice_no, prefix, sequence, type_code = get_next_invoice_number()
        
        # Store the invoice number in session for display
        st.session_state.invoice_meta["invoice_no"] = invoice_no
        st.session_state.invoice_meta["invoice_prefix"] = prefix
        st.session_state.invoice_meta["invoice_sequence"] = sequence
        st.session_state.invoice_meta["invoice_type_code"] = type_code
        
        with ENGINE.begin() as conn:
            # First check what columns exist in invoices table
            query = text("SHOW COLUMNS FROM invoices")
            result = conn.execute(query)
            invoice_columns = [row[0] for row in result.fetchall()]
            
            # Insert invoice header
            # Check if invoice_number_generated column exists
            if 'invoice_number_generated' in invoice_columns:
                # Use invoice_number_generated column
                query = text("""
                    INSERT INTO invoices 
                    (project_id, clientId, type, invoice_number_generated, invoiceNumber, date,
                     subTotal, tax, total, status, createdAt)
                    VALUES (:p, :pt, :t, :no, :inv_no, CURDATE(), 
                            :sub, :tax, :total, 'draft', NOW())
                """)
            else:
                # Only use invoiceNumber column
                query = text("""
                    INSERT INTO invoices 
                    (project_id, clientId, type, invoiceNumber, date,
                     subTotal, tax, total, status, createdAt)
                    VALUES (:p, :pt, :t, :inv_no, CURDATE(), 
                            :sub, :tax, :total, 'draft', NOW())
                """)
            
            params = {
                "p": st.session_state.invoice_meta["project_id"],
                "pt": st.session_state.invoice_meta["party_id"],
                "t": st.session_state.invoice_meta["invoice_type"],
                "inv_no": invoice_no,
                "sub": subtotal,
                "tax": gst_calc["total_gst"],
                "total": gst_calc["grand_total"]
            }
            
            if 'invoice_number_generated' in invoice_columns:
                params["no"] = invoice_no
            
            conn.execute(query, params)
            
            # Get the auto-generated invoice ID
            query = text("SELECT LAST_INSERT_ID()")
            result = conn.execute(query)
            invoice_id = result.fetchone()[0]
            
            # Update stock for each item
            stock_updates = []
            for item in st.session_state.invoice:
                product_name = item["item_description"]
                qty = float(item["qty"])
                
                # Get current stock
                current_stock = get_product_stock(product_name)
                if current_stock is not None:
                    current_stock = float(current_stock)
                    if current_stock >= qty:
                        # Decrease stock
                        new_stock = current_stock - qty
                        update_query = text("""
                            UPDATE boq_items 
                            SET quantity = :new_qty 
                            WHERE LOWER(item_description) = LOWER(:p)
                        """)
                        conn.execute(update_query, {"p": product_name, "new_qty": new_stock})
                        stock_updates.append(f"✅ {product_name}: {current_stock} → {new_stock} (reduced by {qty})")
                    else:
                        stock_updates.append(f"⚠️ {product_name}: Insufficient stock! Available: {current_stock}, Required: {qty}")
            
            # Insert invoice items with UOM
            for item in st.session_state.invoice:
                # Calculate total amount for this item
                item_total = float(item["qty"]) * float(item["supply_rate"])
                
                # Get product ID from boq_items table
                product_id = get_product_id(item["item_description"])
                
                # Get UOM from item or default to 'nos'
                uom = item.get("uom", "nos")
                
                # Insert into invoice_items table with itemId and UOM
                item_query = text("""
                    INSERT INTO invoice_items 
                    (invoiceId, itemId, description, uom, quantity, rate, amount)
                    VALUES (:inv_id, :item_id, :desc, :uom, :qty, :rate, :amount)
                """)
                
                item_params = {
                    "inv_id": invoice_id,
                    "item_id": product_id if product_id else None,  # Use None if product not found
                    "desc": item["item_description"],
                    "uom": uom,
                    "qty": float(item["qty"]),
                    "rate": float(item["supply_rate"]),
                    "amount": item_total
                }
                
                conn.execute(item_query, item_params)
        
        # Update meta
        st.session_state.invoice_meta.update({
            "invoice_no": invoice_no,
            "invoice_prefix": prefix,
            "invoice_sequence": sequence,
            "invoice_type_code": type_code,
            "total_amount": subtotal,
            "cgst": gst_calc["cgst_amount"],
            "sgst": gst_calc["sgst_amount"],
            "igst": gst_calc["igst_amount"],
            "grand_total": gst_calc["grand_total"],
            "invoice_date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Prepare response with stock updates
        response = f"✅ **Invoice #{invoice_no} generated successfully!**\n\n"
        response += f"📋 **Invoice Details:**\n"
        response += f"• **Invoice Number:** `{invoice_no}`\n"
        response += f"• **Project:** {st.session_state.invoice_meta['project_name']}\n"
        response += f"• **Party:** {st.session_state.invoice_meta['party_name']}\n"
        response += f"• **Type:** {st.session_state.invoice_meta['invoice_type']} ({type_code})\n"
        response += f"• **Address:** {st.session_state.invoice_meta['party_address'] or 'N/A'}\n"
        response += f"• **Pincode:** {st.session_state.invoice_meta['party_pincode'] or 'N/A'}\n"
        response += f"• **GST:** {st.session_state.invoice_meta['party_gst'] or 'N/A'}\n"
        response += f"• **Subtotal:** ₹{subtotal:,.2f}\n"
        response += f"• **GST ({gst_calc['gst_type']}):** ₹{gst_calc['total_gst']:,.2f}\n"
        response += f"• **Grand Total:** ₹{gst_calc['grand_total']:,.2f}\n"
        response += f"• **Items:** {len(st.session_state.invoice)}\n"
        response += f"• **Sequence:** {sequence}\n"
        response += f"• **Invoice ID:** {invoice_id}\n\n"
        
        if stock_updates:
            response += "**Stock Updates:**\n"
            for update in stock_updates:
                response += f"• {update}\n"
        
        # Clear invoice after generation
        st.session_state.invoice = []
        st.session_state.stock_alert = []
        
        return True, response
    except Exception as e:
        print(f"Error in save_invoice_to_db: {e}")
        return False, f"Error saving invoice: {str(e)}"

# =========================
# NLP FUNCTIONS
# =========================

def extract_product_qty_price(text):
    """Extract product, quantity, price and UOM from text"""
    text_lower = text.lower().strip()
    
    product = None
    qty = None
    price = None
    uom = None
    
    # Common UOM patterns
    uom_patterns = [
        (r'(\d+)\s*(kg|kilogram|kgs)', 'kg'),
        (r'(\d+)\s*(g|gram|gm)', 'g'),
        (r'(\d+)\s*(mg|milligram)', 'mg'),
        (r'(\d+)\s*(l|liter|litre|lt)', 'l'),
        (r'(\d+)\s*(ml|milliliter)', 'ml'),
        (r'(\d+)\s*(m|meter|metre)', 'm'),
        (r'(\d+)\s*(cm|centimeter)', 'cm'),
        (r'(\d+)\s*(mm|millimeter)', 'mm'),
        (r'(\d+)\s*(pcs|pieces|pc|piece|nos|numbers)', 'nos'),
        (r'(\d+)\s*(box|boxes)', 'box'),
        (r'(\d+)\s*(pack|packs|packet|packets)', 'pack'),
        (r'(\d+)\s*(set|sets)', 'set'),
        (r'(\d+)\s*(roll|rolls)', 'roll'),
        (r'(\d+)\s*(pair|pairs)', 'pair'),
        (r'(\d+)\s*(dozen|dozens)', 'dozen'),
        (r'(\d+)\s*(bundle|bundles)', 'bundle'),
        (r'(\d+)\s*(carton|cartons)', 'carton'),
        (r'(\d+)\s*(bag|bags)', 'bag'),
        (r'(\d+)\s*(tin|tins)', 'tin'),
        (r'(\d+)\s*(can|cans)', 'can'),
        (r'(\d+)\s*(bottle|bottles)', 'bottle'),
        (r'(\d+)\s*(jar|jars)', 'jar'),
        (r'(\d+)\s*(tube|tubes)', 'tube'),
    ]
    
    # First check for UOM patterns
    for pattern, unit in uom_patterns:
        match = re.search(pattern, text_lower)
        if match:
            qty = float(match.group(1))
            uom = unit
            # Remove the matched pattern from text
            text_lower = re.sub(pattern, '', text_lower)
            break
    
    # Check for "more" pattern
    more_match = re.search(r'(.+?)\s+(\d+)\s+more', text_lower)
    if more_match and qty is None:
        product = more_match.group(1).strip()
        qty = float(more_match.group(2))
        # Don't extract price for "more" patterns
        return product, qty, None, uom
    
    # Check for price change patterns
    price_match = re.search(r'(.+?)\s+(?:price|rate)\s+(?:is|to|as)?\s*(\d+(?:\.\d+)?)', text_lower)
    if price_match:
        product = price_match.group(1).strip()
        price = float(price_match.group(2))
        return product, None, price, uom
    
    # Extract price
    price_patterns = [
        r'for\s*(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
        r'at\s*(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
        r'price\s*(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
        r'(?:rs|₹|inr)\s*(\d+(?:\.\d+)?)',
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                price = float(match.group(1))
                text_lower = re.sub(pattern, '', text_lower, count=1)
                break
            except (ValueError, TypeError):
                continue
    
    # Extract quantity if not already extracted from UOM pattern
    if qty is None:
        numbers = re.findall(r'\d+(?:\.\d+)?', text_lower)
        
        if numbers:
            try:
                if price is not None and len(numbers) >= 1:
                    qty = float(numbers[0])
                    text_lower = re.sub(r'\d+(?:\.\d+)?', '', text_lower, count=1)
                elif price is None and len(numbers) == 1:
                    if any(word in text_lower for word in ['for', 'at', 'price', 'rs', '₹', 'inr']):
                        price = float(numbers[0])
                    else:
                        qty = float(numbers[0])
                elif price is None and len(numbers) >= 2:
                    qty = float(numbers[0])
                    price = float(numbers[-1])
            except (ValueError, TypeError):
                # If conversion fails, use defaults
                if qty is None:
                    qty = 1.0
    
    # Extract product
    stop_words = {"i", "need", "want", "add", "order", "give", "me", "please", 
                  "some", "the", "a", "an", "for", "at", "price", "rs", "₹", "inr",
                  "more", "additional", "extra", "increase"}
    
    words = re.findall(r'[a-z]+', text_lower)
    filtered_words = []
    for word in words:
        if word not in stop_words and len(word) > 1:
            filtered_words.append(word)
    
    if filtered_words:
        product = ' '.join(filtered_words).strip()
    
    # Special handling
    if not product:
        patterns = [
            r'(?:need|want|add|order)\s+([a-z]+(?:\s+[a-z]+)?)\s+(?:for|at|price)',
            r'([a-z]+(?:\s+[a-z]+)?)\s+(?:for|at)\s+(?:rs|₹|inr|\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                potential = match.group(1).strip()
                if potential not in stop_words and len(potential) > 1:
                    product = potential
                    break
    
    # Special case: "i need 10 pen for 50 rs"
    if product and price and qty is None:
        start_match = re.match(r'^(\d+)\s+', text.lower())
        if start_match:
            try:
                qty = float(start_match.group(1))
            except (ValueError, TypeError):
                qty = 1.0
        else:
            qty = 1.0
    
    # If UOM is still None but we have a product name that might contain UOM hint
    if uom is None and product:
        # Check product name for common UOM hints
        product_lower = product.lower()
        if any(word in product_lower for word in ['kg', 'kilogram', 'kgs']):
            uom = 'kg'
        elif any(word in product_lower for word in ['g', 'gram', 'gm']):
            uom = 'g'
        elif any(word in product_lower for word in ['l', 'liter', 'litre']):
            uom = 'l'
        elif any(word in product_lower for word in ['ml']):
            uom = 'ml'
        elif any(word in product_lower for word in ['m', 'meter', 'metre']):
            uom = 'm'
        elif any(word in product_lower for word in ['cm']):
            uom = 'cm'
        elif any(word in product_lower for word in ['mm']):
            uom = 'mm'
        elif any(word in product_lower for word in ['box', 'boxes']):
            uom = 'box'
        elif any(word in product_lower for word in ['pack', 'packet']):
            uom = 'pack'
        elif any(word in product_lower for word in ['roll']):
            uom = 'roll'
        else:
            # Default UOM if not specified
            uom = 'nos'
    
    # Ensure we return at least quantity=1 if we have a product
    if product and qty is None:
        qty = 1.0
    
    # Ensure UOM is set
    if product and uom is None:
        uom = 'nos'
    
    # Ensure price is set to something reasonable if not specified
    if product and price is None and qty:
        # Try to get price from database
        exists, db_price, stock = check_product_exists_simple(product)
        if exists and db_price:
            price = float(db_price)
        else:
            price = 0.0  # Default price if not found
    
    return product, qty, price, uom

def smart_product_match(user_input):
    """Match product from input to database"""
    products = get_product_options()
    if not products:
        return None
    
    product, _, _ = extract_product_qty_price(user_input)
    
    if product:
        for p in products:
            if p.lower() == product.lower():
                return p
        
        for p in products:
            if product.lower() in p.lower() or p.lower() in product.lower():
                return p
    
    return product

def get_ai_response(user_message, context_history):
    """Get AI response"""
    if not client:
        user_lower = user_message.lower()
        if any(word in user_lower for word in ["hi", "hello", "hey"]):
            return "Hello! How can I help you today?"
        elif "thank" in user_lower:
            return "You're welcome!"
        elif any(word in user_lower for word in ["bye", "goodbye"]):
            return "Goodbye!"
        else:
            return "I can help you with invoices. What do you need?"
    
    projects = get_projects()
    parties = get_parties()
    products = get_product_options()
    
    system_prompt = f"""You are a helpful invoice assistant. Help users create invoices.
    
    Available:
    Projects: {', '.join([p[1] for p in projects[:3]]) if projects else 'None'}
    Parties: {', '.join([p['name'] for p in parties[:3]]) if parties else 'None'}
    Products: {', '.join(products[:3]) if products else 'None'}
    
    Steps:
    1. Select project
    2. Select party (with address, pincode, GST info)
    3. Select invoice type
    4. Add products
    5. Generate invoice with GST calculation
    
    Be friendly and helpful. Keep responses short."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        *context_history[-4:],
        {"role": "user", "content": user_message}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].message.content
    except:
        return "I can help you create invoices. What do you need?"

def check_product_exists_with_id(product_name):
    """Check if product exists in database and return id, price, stock"""
    try:
        with ENGINE.connect() as conn:
            query = text("SELECT id, supply_rate, quantity FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
            result = conn.execute(query, {"p": product_name})
            row = result.fetchone()
            if row:
                # Convert to appropriate types
                product_id = int(row[0]) if row[0] is not None else None
                price = float(row[1]) if row[1] is not None else None
                stock = float(row[2]) if row[2] is not None else None
                return True, product_id, price, stock
            return False, None, None, None
    except Exception as e:
        print(f"Error checking product with ID: {e}")
        return False, None, None, None

# =========================
# CHAT ENGINE (UPDATED VERSION) - WITH PROMPT COMMANDS FOR UPDATING
# =========================

def add_or_update_invoice_item(product_name, qty, price, uom=None):
    """Add or update item in invoice with all information and check stock"""
    # Validate inputs
    if qty is None or price is None:
        return "invalid_input", None
    
    try:
        qty = float(qty)
        price = float(price)
    except (ValueError, TypeError):
        return "invalid_input", None
    
    # Get UOM from database if not provided
    if uom is None:
        try:
            with ENGINE.connect() as conn:
                query = text("SELECT unit FROM boq_items WHERE LOWER(item_description) = LOWER(:p)")
                result = conn.execute(query, {"p": product_name})
                row = result.fetchone()
                if row and row[0]:
                    uom = row[0]
        except Exception as e:
            print(f"Error getting UOM from database: {e}")
    
    # Default UOM if still None
    if uom is None:
        uom = 'nos'
    
    # Check stock availability
    available_stock = get_product_stock(product_name)
    
    if available_stock is not None:
        try:
            available_stock = float(available_stock)
        except (ValueError, TypeError):
            available_stock = None
        
        if available_stock is not None:
            total_requested = qty
            # Check if product already in invoice
            for item in st.session_state.invoice:
                if item["item_description"].lower() == product_name.lower():
                    item_qty = item.get("qty")
                    if item_qty is not None:
                        try:
                            total_requested += float(item_qty)
                        except (ValueError, TypeError):
                            continue
            
            # Check if stock is sufficient
            if total_requested > available_stock:
                # Add to stock alerts
                st.session_state.stock_alert.append({
                    "product": product_name,
                    "requested": total_requested,
                    "available": available_stock,
                    "shortage": total_requested - available_stock
                })
                return "stock_insufficient", available_stock
    
    # Check if item exists in invoice
    for item in st.session_state.invoice:
        if item["item_description"].lower() == product_name.lower():
            # Update existing item
            item["qty"] = qty
            item["supply_rate"] = price
            item["uom"] = uom
            return "updated", None
    
    # Add new item with all information
    new_item = {
        "item_description": product_name,
        "qty": qty,
        "supply_rate": price,
        "uom": uom
    }
    
    # Add meta info if available
    if st.session_state.invoice_meta["project_name"]:
        new_item["project"] = st.session_state.invoice_meta["project_name"]
    if st.session_state.invoice_meta["party_name"]:
        new_item["party"] = st.session_state.invoice_meta["party_name"]
    if st.session_state.invoice_meta["invoice_type"]:
        new_item["invoice_type"] = st.session_state.invoice_meta["invoice_type"]
    if st.session_state.invoice_meta["party_address"]:
        new_item["party_address"] = st.session_state.invoice_meta["party_address"]
    if st.session_state.invoice_meta["party_pincode"]:
        new_item["party_pincode"] = st.session_state.invoice_meta["party_pincode"]
    if st.session_state.invoice_meta["party_gst"]:
        new_item["party_gst"] = st.session_state.invoice_meta["party_gst"]
    
    st.session_state.invoice.append(new_item)
    return "added", None


def chat_engine(user_text):
    text = user_text.lower().strip()
    
    # Update context
    st.session_state.ai_context.append({"role": "user", "content": user_text})

    # ===========================================
    # NEW: INCREASE QUANTITY COMMAND
    # ===========================================
    if text.startswith("increase") or text.startswith("add more"):
        # Patterns to match:
        # "increase pen by 5"
        # "increase pen quantity by 5"
        # "add more pen 5"
        # "add 5 more pen"
        
        patterns = [
            r'(?:increase|add)\s+(.+?)\s+(?:by|)\s+(\d+)',
            r'(?:increase|add)\s+(\d+)\s+more\s+(.+)',
            r'(?:increase|add)\s+(.+?)\s+quantity\s+(?:by|)\s+(\d+)',
            r'add\s+more\s+(.+?)\s+(\d+)',
        ]
        
        product = None
        additional_qty = None
        
        for pattern in patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Check which pattern matched
                    if pattern == r'(?:increase|add)\s+(\d+)\s+more\s+(.+)':
                        additional_qty = int(match.group(1))
                        product = match.group(2).strip()
                    else:
                        product = match.group(1).strip()
                        additional_qty = int(match.group(2))
                    break
        
        # If pattern not matched, try alternative extraction
        if not product:
            # Extract product and number
            numbers = re.findall(r'\d+', user_text)
            words = re.findall(r'[a-zA-Z]+', user_text)
            
            if numbers and len(words) >= 2:
                additional_qty = int(numbers[0])
                # Find product name (skip "increase", "add", "more", "quantity")
                stop_words = ["increase", "add", "more", "quantity", "by", "to", "additional"]
                product_words = []
                for word in words:
                    if word.lower() not in stop_words:
                        product_words.append(word)
                
                if product_words:
                    product = ' '.join(product_words)
        
        if product and additional_qty:
            # Check if product exists in database
            exists, db_price, current_stock = check_product_exists_simple(product)
            
            if not exists:
                return f"❌ **{product}** not found in database."
            
            # Check if product exists in current invoice
            in_invoice = False
            current_qty = 0
            for item in st.session_state.invoice:
                if item["item_description"].lower() == product.lower():
                    in_invoice = True
                    current_qty = item["qty"]
                    break
            
            if not in_invoice:
                return f"❌ **{product}** not in current invoice. Add it first with 'add {product}'"
            
            # Calculate new total quantity
            new_total_qty = current_qty + additional_qty
            
            # Check stock availability
            if current_stock is not None:
                # Calculate total requested from all invoice items
                total_requested = new_total_qty
                
                # Check other invoice items for same product
                for item in st.session_state.invoice:
                    if item["item_description"].lower() == product.lower():
                        # Already counted in new_total_qty
                        pass
                
                if total_requested > current_stock:
                    return f"❌ **Stock Insufficient!** Only {current_stock} units available, need {total_requested} units."
            
            # Update quantity in invoice
            for item in st.session_state.invoice:
                if item["item_description"].lower() == product.lower():
                    old_qty = item["qty"]
                    item["qty"] = new_total_qty
                    
                    response = f"✅ **Increased {product} quantity:**\n"
                    response += f"• Invoice: {old_qty} → {new_total_qty} (+{additional_qty})\n"
                    
                    # Update database stock (decrease by additional quantity)
                    # Since invoice is not saved yet, we don't update database stock
                    # Stock will be updated when invoice is generated
                    
                    response += f"• Database price: ₹{db_price:,.2f}\n"
                    if current_stock is not None:
                        response += f"• Available stock: {current_stock} units\n"
                        response += f"• Stock check: {current_stock} ≥ {new_total_qty} ✅"
                    
                    return response
            
            return f"❌ Error updating {product} in invoice"
        
        return "❌ Please specify product and quantity. Example: 'increase pen by 5' or 'add 3 more notebook'"
    
    # ===========================================
    # NEW: DELETE ROW COMMAND
    # ===========================================
    if text.startswith("delete") or text.startswith("remove"):
        # Patterns to match:
        # "delete pen"
        # "delete pen row"
        # "remove pen from invoice"
        # "remove pen item"
        
        # Extract product name
        patterns = [
            r'(?:delete|remove)\s+(.+?)\s+(?:row|item|from invoice|line)',
            r'(?:delete|remove)\s+(.+)'
        ]
        
        product = None
        for pattern in patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                product = match.group(1).strip()
                break
        
        # If pattern not matched, try simple extraction
        if not product:
            words = re.findall(r'[a-zA-Z]+', user_text)
            stop_words = ["delete", "remove", "row", "item", "from", "invoice", "line"]
            product_words = []
            for word in words:
                if word.lower() not in stop_words:
                    product_words.append(word)
            
            if product_words:
                product = ' '.join(product_words)
        
        if product:
            # Check if product exists in invoice
            in_invoice = False
            for item in st.session_state.invoice:
                if item["item_description"].lower() == product.lower():
                    in_invoice = True
                    break
            
            if not in_invoice:
                return f"❌ **{product}** not found in current invoice."
            
            # Confirm deletion for important items
            if len(st.session_state.invoice) == 1:
                st.session_state.pending_data = {"product": product}
                st.session_state.chat_stage = "CONFIRM_DELETE_LAST_ITEM"
                return f"⚠️ **This is the last item in your invoice.**\nAre you sure you want to delete '{product}'? (yes/no)"
            
            # Remove the product
            success, message = remove_product_from_invoice(product)
            
            if success:
                # Update invoice totals display
                subtotal = 0
                for item in st.session_state.invoice:
                    qty = item.get("qty")
                    price = item.get("supply_rate")
                    if qty is not None and price is not None:
                        try:
                            subtotal += float(qty) * float(price)
                        except (ValueError, TypeError):
                            continue
                
                response = f"✅ {message}\n\n"
                response += f"**Updated Invoice:**\n"
                response += f"• Items remaining: {len(st.session_state.invoice)}\n"
                response += f"• Subtotal: ₹{subtotal:,.2f}\n"
                
                if st.session_state.invoice:
                    response += "\n**Remaining items:**\n"
                    for i, item in enumerate(st.session_state.invoice, 1):
                        response += f"{i}. {item['item_description']} - {item['qty']} × ₹{item['supply_rate']:,.2f}\n"
                
                return response
            else:
                return message
        
        return "❌ Please specify which product to delete. Example: 'delete pen' or 'remove notebook row'"



    
    # ===========================================
    # NEW: PROMPT COMMANDS FOR UPDATING INVOICE AND DATABASE
    # ===========================================
    
    # UPDATE QUANTITY IN INVOICE AND DATABASE
    if text.startswith("update") or text.startswith("change"):
        # Extract product and value
        patterns = [
            r'(?:update|change)\s+(.+?)\s+(?:quantity|qty|qty\.)\s+(?:to|by|as)\s+(\d+(?:\.\d+)?)',
            r'(?:update|change)\s+(.+?)\s+(?:price|rate)\s+(?:to|by|as)\s+(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
            r'set\s+(.+?)\s+(?:quantity|qty|qty\.)\s+(?:to|as)\s+(\d+(?:\.\d+)?)',
            r'set\s+(.+?)\s+(?:price|rate)\s+(?:to|as)\s+(?:rs|₹|inr)?\s*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                product = match.group(1).strip()
                value = float(match.group(2))
                
                # Determine what to update
                is_price = any(word in user_text.lower() for word in ["price", "rate"])
                is_quantity = any(word in user_text.lower() for word in ["quantity", "qty", "qty."])
                
                # Check if product exists in database - FIX THIS LINE
                exists, db_price, db_stock = check_product_exists_simple(product)  # Use the 3-value version
                
                if not exists:
                    return f"❌ **{product}** not found in database."
                
                # Prepare response based on what's being updated
                if is_quantity:
                    # Update quantity in invoice
                    updated_in_invoice = False
                    for item in st.session_state.invoice:
                        if item["item_description"].lower() == product.lower():
                            old_qty = item["qty"]
                            item["qty"] = value
                            updated_in_invoice = True
                            break
                    
                    # Update database stock (set new quantity)
                    success, message = update_product_stock(product, value)
                    
                    response = f"✅ **Updated {product}:**\n"
                    if updated_in_invoice:
                        response += f"• Invoice quantity: {old_qty} → {value}\n"
                    response += f"• Database stock: {db_stock} → {value}\n"
                    
                    # Update stock alert if needed
                    if value > db_stock:
                        response += f"⚠️ **Note:** New quantity ({value}) is higher than old stock ({db_stock})"
                    
                    return response
                
                elif is_price:
                    # Update price in invoice
                    updated_in_invoice = False
                    for item in st.session_state.invoice:
                        if item["item_description"].lower() == product.lower():
                            old_price = item["supply_rate"]
                            item["supply_rate"] = value
                            updated_in_invoice = True
                            break
                    
                    # Update database price
                    success, message = update_product_price(product, value)
                    
                    response = f"✅ **Updated {product} price:**\n"
                    if updated_in_invoice:
                        response += f"• Invoice price: ₹{old_price:,.2f} → ₹{value:,.2f}\n"
                    response += f"• Database price: ₹{db_price:,.2f} → ₹{value:,.2f}\n"
                    
                    # Calculate percentage change
                    if db_price and db_price > 0:
                        price_diff = ((value - db_price) / db_price) * 100
                        response += f"• Change: {price_diff:+.1f}%"
                    
                    return response
        
        # If pattern not matched, try alternative extraction
        product = smart_product_match(user_text)
        if product:
            # Extract numbers from text
            numbers = re.findall(r'\d+(?:\.\d+)?', user_text)
            if numbers:
                value = float(numbers[0])
                
                # Guess what to update based on context
                if any(word in user_text.lower() for word in ["price", "rate", "₹", "rs", "inr"]):
                    # Update price
                    exists, db_price, db_stock = check_product_exists(product)
                    if exists:
                        # Update invoice
                        updated = False
                        for item in st.session_state.invoice:
                            if item["item_description"].lower() == product.lower():
                                old_price = item["supply_rate"]
                                item["supply_rate"] = value
                                updated = True
                                break
                        
                        # Update database
                        success, message = update_product_price(product, value)
                        
                        response = f"✅ **Updated {product} price to ₹{value:,.2f}**\n"
                        if updated:
                            response += f"• Invoice updated\n"
                        response += f"• Database updated (from ₹{db_price:,.2f})"
                        return response
                    else:
                        return f"❌ **{product}** not found in database."
                else:
                    # Update quantity
                    exists, db_price, db_stock = check_product_exists(product)
                    if exists:
                        # Update invoice
                        updated = False
                        for item in st.session_state.invoice:
                            if item["item_description"].lower() == product.lower():
                                old_qty = item["qty"]
                                item["qty"] = value
                                updated = True
                                break
                        
                        # Update database
                        success, message = update_product_stock(product, value)
                        
                        response = f"✅ **Updated {product} quantity to {value}**\n"
                        if updated:
                            response += f"• Invoice updated\n"
                        response += f"• Database stock updated (from {db_stock})"
                        return response
                    else:
                        return f"❌ **{product}** not found in database."
                    

    # Add this to chat engine for testing
    if text == "test type mapping":
        test_types = ["purchase", "purchase_order", "sales", "credit", "debit", "delivery_challan"]
        
        response = "🔍 **Type Mapping Test:**\n\n"
        for t in test_types:
            code = get_type_code(t)
            response += f"• **'{t}'** → **'{code}'**\n"
            response += f"  Example: ICE/2025-2026/{code}/0001\n\n"
        
        # Also test with current session type
        current_type = st.session_state.invoice_meta.get("invoice_type")
        if current_type:
            current_code = get_type_code(current_type)
            response += f"\n**Current session type:** '{current_type}' → '{current_code}'\n"
        
        return response                
    
    # ===========================================
    # PROACTIVE PRICE COMPARISON DETECTION
    # ===========================================
    # Check if user is mentioning prices for existing products
    if not st.session_state.chat_stage and not st.session_state.awaiting_choice:
        # Try to extract product and price from natural language
        product, qty, price, uom = extract_product_qty_price(user_text)
        
        if product and price:
            exists, db_price, stock = check_product_exists_simple(product)  # This should be correct
            
            if exists and db_price:
                # FIX: Convert both to float for calculation
                try:
                    db_price_float = float(db_price)
                    price_float = float(price)
                    price_diff = ((price_float - db_price_float) / db_price_float) * 100
                except (ValueError, TypeError):
                    # If conversion fails, skip price comparison
                    price_diff = 0
                
                # Show notification for significant differences
                if abs(price_diff) > 5:  # More than 5% difference
                    if price_float < db_price_float:
                        # Lower price detected
                        st.session_state.pending_data = {
                            "product": product,
                            "qty": qty or 1,
                            "user_price": price_float,
                            "db_price": db_price_float,
                            "diff_percent": abs(price_diff),
                            "from_natural_language": True
                        }
                        
                        if price_diff < -20:  # More than 20% lower
                            response = f"⚠️ **Alert: Very Low Price Mentioned!**\n"
                            response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
                            response += f"Database price: ₹{db_price_float:,.2f}\n"
                            response += f"**Difference:** {abs(price_diff):.1f}% lower\n\n"
                            response += "Options:\n"
                            response += "• Type 'add' to add with your price\n"
                            response += "• Type 'use db' to use database price\n"
                            response += "• Type 'check' to verify stock\n"
                            st.session_state.chat_stage = "PRICE_ALERT_LOW"
                        else:
                            response = f"📉 **Note: Lower Price Mentioned**\n"
                            response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
                            response += f"Database price: ₹{db_price_float:,.2f}\n"
                            response += f"({abs(price_diff):.1f}% lower)\n\n"
                            response += "Shall I use your price? (yes/no)"
                            st.session_state.chat_stage = "PRICE_ALERT_SMALL_LOW"
                        
                        return response
                    
                    elif price_float > db_price_float:
                        # Higher price detected
                        st.session_state.pending_data = {
                            "product": product,
                            "qty": qty or 1,
                            "user_price": price_float,
                            "db_price": db_price_float,
                            "diff_percent": price_diff,
                            "from_natural_language": True
                        }
                        
                        if price_diff > 50:  # More than 50% higher
                            response = f"💰 **Alert: High Price Mentioned!**\n"
                            response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
                            response += f"Database price: ₹{db_price_float:,.2f}\n"
                            response += f"**Difference:** {price_diff:.1f}% higher\n\n"
                            response += "Options:\n"
                            response += "• Type 'add' to add with higher price\n"
                            response += "• Type 'update' to update database price\n"
                            response += "• Type 'use db' to use database price\n"
                            st.session_state.chat_stage = "PRICE_ALERT_HIGH"
                        else:
                            response = f"📈 **Note: Higher Price Mentioned**\n"
                            response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
                            response += f"Database price: ₹{db_price_float:,.2f}\n"
                            response += f"({price_diff:.1f}% higher)\n\n"
                            response += "Update database to new price? (update/use db)"
                            st.session_state.chat_stage = "PRICE_ALERT_SMALL_HIGH"
                        
                        return response
                    
                    elif price_float > db_price_float:
                        # Higher price detected
                        st.session_state.pending_data = {
                            "product": product,
                            "qty": qty or 1,
                            "user_price": price_float,
                            "db_price": db_price_float,
                            "diff_percent": price_diff,
                            "from_natural_language": True
                        }
                        
                        if price_diff > 50:  # More than 50% higher
                            response = f"💰 **Alert: High Price Mentioned!**\n"
                            response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
                            response += f"Database price: ₹{db_price_float:,.2f}\n"
                            response += f"**Difference:** {price_diff:.1f}% higher\n\n"
                            response += "Options:\n"
                            response += "• Type 'add' to add with higher price\n"
                            response += "• Type 'update' to update database price\n"
                            response += "• Type 'use db' to use database price\n"
                            st.session_state.chat_stage = "PRICE_ALERT_HIGH"
                        else:
                            response = f"📈 **Note: Higher Price Mentioned**\n"
                            response += f"You mentioned **{product}** at ₹{price_float:,.2f}\n"
                            response += f"Database price: ₹{db_price_float:,.2f}\n"
                            response += f"({price_diff:.1f}% higher)\n\n"
                            response += "Update database to new price? (update/use db)"
                            st.session_state.chat_stage = "PRICE_ALERT_SMALL_HIGH"
                        
                        return response
    
    # ===========================================
    # HANDLE PRICE ALERT RESPONSES
    # ===========================================
    if st.session_state.chat_stage == "PRICE_ALERT_LOW":
        if text in ["add", "yes", "y", "ok"]:
            p = st.session_state.pending_data
            # Check stock
            stock = get_product_stock(p["product"])
            if stock is not None and p["qty"] > stock:
                return f"❌ **Stock Insufficient!** Only {stock} units available for {p['product']}"
            
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}** (DB: ₹{p['db_price']}). Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}** (DB: ₹{p['db_price']})"
        
        elif text in ["use db", "db", "database", "no", "n"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
        elif text == "check":
            p = st.session_state.pending_data
            stock = get_product_stock(p["product"])
            if stock is not None:
                return f"📦 **Stock for {p['product']}:** {stock} units available\n\nNow type 'add' or 'use db'"
            else:
                return f"❌ **{p['product']}** not found in database"
        
        else:
            st.session_state.chat_stage = None
            return "❌ Cancelled price check."
    
    elif st.session_state.chat_stage == "PRICE_ALERT_SMALL_LOW":
        if text in ["yes", "y", "ok", "add"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}**. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **your price ₹{p['user_price']}**"
        
        elif text in ["no", "n", "db"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
        else:
            st.session_state.chat_stage = None
            return "❌ Using database price."
    
    elif st.session_state.chat_stage == "PRICE_ALERT_HIGH":
        if text in ["add", "yes", "y"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}**. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}**"
        
        elif text == "update":
            p = st.session_state.pending_data
            success, message = update_product_price(p["product"], p["user_price"])
            if success:
                action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
                st.session_state.chat_stage = None
                
                if action == "stock_insufficient":
                    return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
                elif action == "updated":
                    total_qty = sum(item['qty'] for item in st.session_state.invoice 
                                if item['item_description'].lower() == p["product"].lower())
                    return f"✅ **Database price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}. Total now {total_qty}"
                else:
                    return f"✅ **Database price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}"
            else:
                return f"❌ {message}"
        
        elif text in ["use db", "db", "database", "no", "n"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
        else:
            st.session_state.chat_stage = None
            return "❌ Using database price."
    
    elif st.session_state.chat_stage == "PRICE_ALERT_SMALL_HIGH":
        if text == "update":
            p = st.session_state.pending_data
            success, message = update_product_price(p["product"], p["user_price"])
            if success:
                action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
                st.session_state.chat_stage = None
                
                if action == "stock_insufficient":
                    return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
                elif action == "updated":
                    total_qty = sum(item['qty'] for item in st.session_state.invoice 
                                if item['item_description'].lower() == p["product"].lower())
                    return f"✅ **Price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}. Total now {total_qty}"
                else:
                    return f"✅ **Price updated** to ₹{p['user_price']}\n✅ Added {p['qty']} {p['product']}"
            else:
                return f"❌ {message}"
        
        elif text in ["use db", "db", "database", "no", "n"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        
        else:
            st.session_state.chat_stage = None
            return "❌ Using database price."
    
    # ===========================================
    # EXISTING FUNCTIONALITY (REST OF THE CHAT ENGINE)
    # ===========================================
    
    # Greetings
    if text in ["hi", "hello", "hey"]:
        response = "👋 Hello! I can help you create invoices with automatic GST calculation. Type 'generate invoice' to start or 'view invoice [number]' to see old invoices."
        st.session_state.ai_context.append({"role": "assistant", "content": response})
        return response
    
    # STOCK MANAGEMENT COMMANDS
    if text.startswith("add stock") or text.startswith("increase stock"):
        # Extract product and quantity
        match = re.search(r'add stock\s+(.+?)\s+by\s+(\d+)', user_text, re.IGNORECASE)
        if not match:
            match = re.search(r'increase stock\s+(.+?)\s+by\s+(\d+)', user_text, re.IGNORECASE)
        
        if not match:
            # Try alternative pattern
            numbers = re.findall(r'\d+', user_text)
            words = re.findall(r'[a-zA-Z]+', user_text)
            
            if len(numbers) >= 1 and len(words) >= 3:
                product = ' '.join(words[2:])  # Skip "add stock"
                qty = int(numbers[0])
                success, message = increase_product_stock(product, qty)
                return message
        
        if match:
            product = match.group(1).strip()
            qty = int(match.group(2))
            success, message = increase_product_stock(product, qty)
            return message
        
        return "❌ Please specify product and quantity. Example: 'add stock pen by 10' or 'increase stock notebook by 5'"
    
    if text.startswith("check stock"):
        # Extract product name
        product_match = re.search(r'check stock\s+(.+)', user_text, re.IGNORECASE)
        if product_match:
            product_name = product_match.group(1).strip()
            stock = get_product_stock(product_name)
            if stock is not None:
                return f"📦 **Stock for {product_name}:** {stock} units"
            else:
                return f"❌ Product '{product_name}' not found in database"
        else:
            return "❌ Please specify product name. Example: 'check stock pen'"
    
    if text.startswith("set stock") or text.startswith("update stock"):
        # Extract product and quantity
        match = re.search(r'(?:set|update) stock\s+(.+?)\s+to\s+(\d+)', user_text, re.IGNORECASE)
        if match:
            product = match.group(1).strip()
            qty = int(match.group(2))
            success, message = update_product_stock(product, qty)
            return message
        return "❌ Please specify product and quantity. Example: 'set stock pen to 50'"
    

    # ===========================================
    # NEW: CONFIRM DELETE LAST ITEM
    # ===========================================
    if st.session_state.chat_stage == "CONFIRM_DELETE_LAST_ITEM":
        if text in ["yes", "y", "confirm", "ok", "okay"]:
            p = st.session_state.pending_data
            success, message = remove_product_from_invoice(p["product"])
            st.session_state.chat_stage = None
            
            if success:
                return f"✅ {message}\n\nInvoice is now empty. Add new items to continue."
            else:
                return message
        else:
            st.session_state.chat_stage = None
            return "❌ Deletion cancelled. Item kept in invoice."

    
    # PRICE VALIDATION CONFIRMATION
    if st.session_state.chat_stage == "CONFIRM_LOW_PRICE":
        if text in ["yes", "ok", "okay", "confirm", "y", "proceed"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **lower price ₹{p['user_price']}** (DB: ₹{p['db_price']}). Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **lower price ₹{p['user_price']}** (DB: ₹{p['db_price']})"
        else:
            st.session_state.chat_stage = None
            return "❌ Order cancelled. Using database price."

    if st.session_state.chat_stage == "CONFIRM_HIGH_PRICE":
        if text in ["yes", "ok", "okay", "confirm", "y"]:
            p = st.session_state.pending_data
            # Optionally update database price
            if p.get("update_db", False):
                success, _ = update_product_price(p["product"], p["user_price"])
            
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                msg = f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}** (DB: ₹{p['db_price']}). Total now {total_qty}"
                if p.get("update_db", False):
                    msg += f"\n✅ Database price updated to ₹{p['user_price']}"
                return msg
            else:
                msg = f"✅ Added {p['qty']} {p['product']} at **higher price ₹{p['user_price']}** (DB: ₹{p['db_price']})"
                if p.get("update_db", False):
                    msg += f"\n✅ Database price updated to ₹{p['user_price']}"
                return msg
        elif text in ["no", "cancel", "n", "use db"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                            if item['item_description'].lower() == p["product"].lower())
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at **database price ₹{p['db_price']}**"
        else:
            st.session_state.chat_stage = None
            return "❌ Using database price."
        
    # In the chat engine, add a debug command for invoices:
    if text.startswith("debug invoices"):
        invoices = debug_all_invoice_numbers()
        if isinstance(invoices, str):
            return f"❌ {invoices}"
        
        response = "🔍 **All Invoices in Database:**\n\n"
        for inv in invoices:
            response += f"• **ID:** {inv['id']}\n"
            response += f"  **invoiceNumber:** '{inv['invoiceNumber']}'\n"
            response += f"  **invoice_number_generated:** '{inv['invoice_number_generated']}'\n"
            response += f"  **Type:** {inv['type']}, **Date:** {inv['date']}, **Total:** ₹{inv['total']:,.2f}\n"
            response += f"  **Status:** {inv['status']}, **Created:** {inv['createdAt']}\n"
            response += "  ---\n"
        
        response += f"\nTotal shown: {len(invoices)}"
        return response
    
    # VIEW OLD INVOICE
    if text.startswith("view invoice") or text.startswith("show invoice"):
        # Extract the complete invoice number including special characters
        match = re.search(r'(?:view invoice|show invoice)\s+(.+)', user_text, re.IGNORECASE)
        
        if not match:
            return "❌ Please provide an invoice number. Example: 'view invoice ICE/25-26/INV/0018'"
        
        invoice_no = match.group(1).strip()
        
        # First try to get the invoice
        invoice_data = get_invoice_by_number(invoice_no)
        
        if not invoice_data:
            # Try to get list of similar invoices
            try:
                with ENGINE.connect() as conn:
                    # Get all invoice numbers
                    query = text("""
                        SELECT DISTINCT invoiceNumber 
                        FROM invoices 
                        WHERE invoiceNumber IS NOT NULL 
                        ORDER BY invoiceNumber
                    """)
                    result = conn.execute(query)
                    all_invoices = [row[0] for row in result.fetchall() if row[0]]
                    
                    # Find similar invoices
                    similar = []
                    for inv in all_invoices:
                        if invoice_no.lower() in str(inv).lower():
                            similar.append(inv)
                        elif str(inv).lower().startswith(invoice_no.lower()):
                            similar.append(inv)
                    
                    if similar:
                        response = f"❌ **Invoice '{invoice_no}' not found.**\n\n"
                        response += "**Similar invoices in database:**\n"
                        for inv in similar[:5]:  # Show top 5 matches
                            response += f"• {inv}\n"
                        response += "\nTry one of these exact invoice numbers."
                    else:
                        response = f"❌ **Invoice '{invoice_no}' not found in database.**\n\n"
                        response += "**Available invoice numbers:**\n"
                        for inv in all_invoices[:10]:  # Show first 10
                            response += f"• {inv}\n"
                        if len(all_invoices) > 10:
                            response += f"\n... and {len(all_invoices) - 10} more"
                        response += "\n\nType 'debug invoices' to see all invoices with details."
                    
                    return response
            except Exception as e:
                return f"❌ Invoice '{invoice_no}' not found. Error: {str(e)}"
        
        # Store old invoice data in session
        st.session_state.viewing_old_invoice = True
        st.session_state.old_invoice_data = invoice_data
        
        response = f"✅ **Invoice #{invoice_data['header']['invoice_no']} Found!**\n\n"
        response += f"**Project:** {invoice_data['header']['project_name']}\n"
        response += f"**Party:** {invoice_data['header']['party_name']}\n"
        response += f"**Type:** {invoice_data['header']['invoice_type']}\n"
        response += f"**Date:** {invoice_data['header']['invoice_date']}\n"
        response += f"**Subtotal:** ₹{invoice_data['header']['subtotal']:,.2f}\n"
        response += f"**Tax (GST):** ₹{invoice_data['header']['tax']:,.2f}\n"
        response += f"**Grand Total:** ₹{invoice_data['header']['grand_total']:,.2f}\n"
        response += f"**Items:** {len(invoice_data['items'])}\n\n"
        response += "Check the invoice details below 👇"
        
        return response
    
    # LIST ALL INVOICES
    if text.startswith("list invoices") or text == "invoices":
        invoices = get_all_invoices()
        if not invoices:
            return "❌ No invoices found in database."
        
        response = "📋 **All Invoices:**\n\n"
        
        for i, inv in enumerate(invoices, 1):
            # Get invoice number (prefer invoice_number_generated if available)
            invoice_no = inv.get('invoice_generated') or inv.get('invoice_no') or "N/A"
            
            response += f"**{i}. Invoice: {invoice_no}**\n"
            response += f"   📅 **Date:** {inv.get('invoice_date', 'N/A')}\n"
            response += f"   🏢 **Project:** {inv.get('project_name', 'N/A')}\n"
            response += f"   👥 **Party:** {inv.get('party_name', 'N/A')}\n"
            response += f"   📄 **Type:** {inv.get('invoice_type', 'N/A')}\n"
            response += f"   💰 **Total:** ₹{float(inv.get('grand_total', 0)):,.2f}\n"
            response += f"   📊 **Subtotal:** ₹{float(inv.get('subtotal', 0)):,.2f}\n"
            response += f"   🏷️ **Tax:** ₹{float(inv.get('tax_amount', 0)):,.2f}\n"
            response += f"   🕐 **Created:** {inv.get('datetime_display', 'N/A')}\n"
            response += f"   📈 **Status:** {inv.get('status', 'N/A')}\n"
            
            # Add sequence info if available
            if inv.get('invoice_prefix') and inv.get('invoice_sequence'):
                response += f"   🔢 **Sequence:** {inv['invoice_prefix']}/{inv['invoice_sequence']}\n"
            
            response += f"   🔗 **ID:** {inv.get('project_id', 'N/A')}/{inv.get('party_id', 'N/A')}\n"
            response += "   ---\n\n"
        
        response += f"\n**Total Invoices:** {len(invoices)}\n"
        response += "To view details, type: 'view invoice [invoice-number]'\n"
        response += "Example: 'view invoice ICE/25-26/INV/0018'"
        
        return response
    
    # GENERATE INVOICE FLOW START
    if "generate invoice" in text or "create invoice" in text:
        projects = get_projects()
        if not projects:
            return "❌ No projects found in database. Please add projects first."
        
        st.session_state.invoice_flow = "GENERATING"
        st.session_state.choice_type = "PROJECT"
        st.session_state.choice_options = projects
        st.session_state.awaiting_choice = True
        
        response = "🏗️ **Select a Project:**\n\n"
        for i, (id, name) in enumerate(projects, 1):
            response += f"{i}. {name}\n"
        response += "\nReply with number (1, 2, 3...)"
        
        return response
    
    # DEBUG COMMANDS
    if text.startswith("debug tables"):
        tables = debug_database_tables()
        if isinstance(tables, str):
            return f"❌ {tables}"
        
        response = "🔍 **Database Tables:**\n\n"
        for i, table in enumerate(tables, 1):
            response += f"{i}. {table}\n"
        
        return response
    
    if text.startswith("debug table"):
        # Extract table name
        match = re.search(r'debug table\s+(.+)', user_text, re.IGNORECASE)
        if not match:
            return "❌ Please provide a table name. Example: 'debug table parties'"
        
        table_name = match.group(1).strip()
        debug_info = debug_table_structure(table_name)
        
        if isinstance(debug_info, str):
            return f"❌ {debug_info}"
        
        response = f"🔍 **Table Structure: {table_name}**\n\n"
        response += "**Columns:**\n"
        for col in debug_info["columns"]:
            response += f"• {col['field']} ({col['type']}) - Null: {col['null']}\n"
        
        response += "\n**Sample Data (first 3 rows):**\n"
        for i, row in enumerate(debug_info["sample_data"], 1):
            response += f"{i}. {row}\n"
        
        return response
    
    if text.startswith("debug search"):
        invoices = debug_search_invoices()
        if isinstance(invoices, str):
            return f"❌ {invoices}"
        
        response = "🔍 **Debug - All Invoice Numbers in Database:**\n\n"
        for inv in invoices:
            response += f"• **invoice_number_generated:** '{inv['invoice_number_generated']}' "
            response += f"(UPPER: '{inv['upper_generated']}')\n"
            response += f"  **invoiceNumber:** '{inv['invoiceNumber']}' "
            response += f"(UPPER: '{inv['upper_number']}')\n"
            response += f"  **Date:** {inv['date']}, **Type:** {inv['type']}, **Total:** ₹{inv['total']:,.2f}\n"
            response += "  ---\n"
        
        response += f"\nTotal found: {len(invoices)}"
        return response
    
    if text.startswith("check invoice"):
        # Extract invoice number
        match = re.search(r'check invoice\s+(.+)', user_text, re.IGNORECASE)
        if not match:
            return "❌ Please provide an invoice number. Example: 'check invoice ICE/25-26/PO/020'"
        
        invoice_no = match.group(1).strip()
        
        try:
            with ENGINE.connect() as conn:
                # Check if invoice exists in invoiceNumber column
                query = text("""
                    SELECT invoiceNumber, invoice_number_generated, type, date, total, status, clientId, project_id
                    FROM invoices 
                    WHERE invoiceNumber = :no
                    LIMIT 1
                """)
                result = conn.execute(query, {"no": invoice_no})
                row = result.fetchone()
                
                if row:
                    response = f"✅ **Invoice Found in Database:**\n\n"
                    response += f"**invoiceNumber:** '{row[0]}'\n"
                    response += f"**invoice_number_generated:** '{row[1]}'\n"
                    response += f"**Type:** {row[2]}\n"
                    response += f"**Date:** {row[3]}\n"
                    response += f"**Total:** ₹{float(row[4]) if row[4] else 0:,.2f}\n"
                    response += f"**Status:** {row[5]}\n"
                    response += f"**Client ID:** {row[6]}\n"
                    response += f"**Project ID:** {row[7]}"
                    return response
                else:
                    # Try with LIKE search
                    query = text("""
                        SELECT invoiceNumber, invoice_number_generated, type, date, total, status
                        FROM invoices 
                        WHERE invoiceNumber LIKE :pattern
                        LIMIT 5
                    """)
                    result = conn.execute(query, {"pattern": f"%{invoice_no}%"})
                    rows = result.fetchall()
                    
                    if rows:
                        response = f"🔍 **Similar invoices found for '{invoice_no}':**\n\n"
                        for r in rows:
                            response += f"• **{r[0]}** - {r[2]} - {r[3]} - ₹{float(r[4]) if r[4] else 0:,.2f}\n"
                        return response
                    else:
                        return f"❌ Invoice **{invoice_no}** not found in invoiceNumber column."
        except Exception as e:
            return f"❌ Error: {e}"
    
    if text.startswith("search invoices"):
        search_term = text.replace("search invoices", "").strip()
        if not search_term:
            return "❌ Please provide a search term"
        
        try:
            with ENGINE.connect() as conn:
                query = text("""
                    SELECT invoiceNumber, type, date, total, status, clientId, project_id
                    FROM invoices 
                    WHERE invoiceNumber LIKE :pattern
                    ORDER BY createdAt DESC
                    LIMIT 10
                """)
                result = conn.execute(query, {"pattern": f"%{search_term}%"})
                rows = result.fetchall()
                
                if not rows:
                    return f"❌ No invoices found containing '{search_term}'"
                
                response = f"🔍 **Invoices containing '{search_term}':**\n\n"
                for i, row in enumerate(rows, 1):
                    response += f"{i}. **{row[0]}** - {row[1]} - {row[2]} - ₹{float(row[3]) if row[3] else 0:,.2f} - {row[4]}\n"
                    response += f"   Client ID: {row[5]}, Project ID: {row[6]}\n"
                
                response += f"\n**Total found:** {len(rows)}"
                return response
        except Exception as e:
            return f"❌ Error: {e}"
    
    # HANDLE CHOICE SELECTIONS
    if st.session_state.awaiting_choice and text.isdigit():
        idx = int(text) - 1
        
        if idx < 0 or idx >= len(st.session_state.choice_options):
            return "❌ Invalid selection. Please choose a valid number."
        
        if st.session_state.choice_type == "PROJECT":
            # Project selected
            project_id, project_name = st.session_state.choice_options[idx]
            st.session_state.invoice_meta["project_id"] = project_id
            st.session_state.invoice_meta["project_name"] = project_name
            
            # Get parties with address info
            parties = get_parties()
            if not parties:
                st.session_state.awaiting_choice = False
                st.session_state.choice_type = None
                return "❌ No parties found in database. Please add parties first."
            
            st.session_state.choice_type = "PARTY"
            st.session_state.choice_options = parties
            st.session_state.awaiting_choice = True
            
            response = f"✅ **Project Selected:** {project_name}\n\n"
            response += "👥 **Select a Party:**\n\n"
            for i, party in enumerate(parties, 1):
                # Safely display party info
                party_display = f"{i}. {party['name']}"
                
                # Add pincode if available
                if party.get("pincode"):
                    party_display += f" [{party['pincode']}]"
                
                # Add truncated address if available
                if party.get("address"):
                    address = party['address']
                    if len(address) > 30:
                        party_display += f" - {address[:30]}..."
                    else:
                        party_display += f" - {address}"
                
                response += party_display + "\n"
            response += "\nReply with number (1, 2, 3...)"
            
            return response
        
        elif st.session_state.choice_type == "PARTY":
            # Party selected - GET ADDRESS, PINCODE, GST INFO
            party = st.session_state.choice_options[idx]
            st.session_state.invoice_meta["party_id"] = party["id"]
            st.session_state.invoice_meta["party_name"] = party["name"]
            st.session_state.invoice_meta["party_address"] = party.get("address")
            st.session_state.invoice_meta["party_pincode"] = party.get("pincode")
            st.session_state.invoice_meta["party_gst"] = party.get("gst")
            
            # Show party details including address
            party_details = f"✅ **Party Selected:** {party['name']}\n"
            if party.get("address"):
                party_details += f"**Address:** {party['address']}\n"
            if party.get("pincode"):
                party_details += f"**Pincode:** {party['pincode']}\n"
            if party.get("gst"):
                party_details += f"**GST:** {party['gst']}\n"
            
            # Get invoice types
            invoice_types = get_invoice_types()
            st.session_state.choice_type = "INVOICE_TYPE"
            st.session_state.choice_options = invoice_types
            st.session_state.awaiting_choice = True
            
            response = party_details + "\n"
            response += "📄 **Select Invoice Type:**\n\n"
            for i, inv_type in enumerate(invoice_types, 1):
                response += f"{i}. {inv_type}\n"
            response += "\nReply with number (1, 2, 3...)"
            
            return response
        
        # In the chat engine, find the INVOICE_TYPE selection part and update it:
        elif st.session_state.choice_type == "INVOICE_TYPE":
            # Invoice type selected - extract just the base type (before parentheses)
            invoice_type_with_code = st.session_state.choice_options[idx]
            
            # Extract just the type name (before parentheses if present)
            if "(" in invoice_type_with_code:
                # Extract the part before parentheses
                invoice_type = invoice_type_with_code.split("(")[0].strip()
            else:
                invoice_type = invoice_type_with_code.strip()
            
            # Store the clean type
            st.session_state.invoice_meta["invoice_type"] = invoice_type
            
            # Get the type code for display
            type_code = get_type_code(invoice_type)
            
            # Clear choice state
            st.session_state.awaiting_choice = False
            st.session_state.choice_type = None
            st.session_state.choice_options = []
            st.session_state.invoice_flow = None
            
            response = f"✅ **Invoice Setup Complete!**\n\n"
            response += f"**Project:** {st.session_state.invoice_meta['project_name']}\n"
            response += f"**Party:** {st.session_state.invoice_meta['party_name']}\n"
            
            # Show address if available
            if st.session_state.invoice_meta["party_address"]:
                response += f"**Address:** {st.session_state.invoice_meta['party_address']}\n"
            
            # Extract pincode from address if not in party_pincode
            pincode = st.session_state.invoice_meta["party_pincode"]
            
            # If no pincode in party data, try to extract from address
            if not pincode and st.session_state.invoice_meta["party_address"]:
                address = st.session_state.invoice_meta["party_address"]
                # Look for 6-digit number in address
                pincode_match = re.search(r'(\d{6})', address)
                if pincode_match:
                    pincode = pincode_match.group(1)
                    st.session_state.invoice_meta["party_pincode"] = pincode
            
            # Show pincode if found
            if pincode:
                response += f"**Pincode:** {pincode}\n"
                # Show GST type based on pincode
                gst_info = get_gst_rate_from_pincode(pincode)
                response += f"**GST Type:** {gst_info['type']} ({gst_info['total_gst_rate']}%)\n"
            
            # Show GST number only if it looks like a GST
            if st.session_state.invoice_meta["party_gst"]:
                gst = st.session_state.invoice_meta["party_gst"]
                if re.match(r'^[0-9A-Z]{10,}$', gst):
                    response += f"**GST Number:** {gst}\n"
            
            response += f"**Invoice Type:** {invoice_type} ({type_code})\n\n"
            response += "Now you can add products. Example: 'i need 10 pen for 50 rs'"
            
            return response
    
    # PRODUCT PRICE CHANGE CONFIRMATION
    if st.session_state.chat_stage == "CONFIRM_PRICE_CHANGE":
        if text in ["yes", "ok", "okay", "confirm", "y"]:
            p = st.session_state.pending_data
            success, message = update_product_price(p["product"], p["new_price"])
            if success:
                for item in st.session_state.invoice:
                    if item["item_description"].lower() == p["product"].lower():
                        item["supply_rate"] = p["new_price"]
                
                st.session_state.chat_stage = None
                return f"✅ Price of **{p['product']}** updated to ₹{p['new_price']}"
            else:
                st.session_state.chat_stage = None
                return f"❌ {message}"
        else:
            st.session_state.chat_stage = None
            return "❌ Price update cancelled."
    
    # CONFIRM PRICE CHANGE FOR ORDER
    if st.session_state.chat_stage == "CONFIRM_PRICE_CHANGE_FOR_ORDER":
        if text in ["yes", "ok", "okay", "confirm", "y"]:
            p = st.session_state.pending_data
            success, _ = update_product_price(p["product"], p["user_price"])
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["user_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                              if item['item_description'].lower() == p["product"].lower())
                return f"✅ Price updated to ₹{p['user_price']} and quantity increased by {p['qty']}. Total now {total_qty}"
            else:
                return f"✅ Price updated to ₹{p['user_price']} and added {p['qty']} {p['product']} to invoice"
        elif text in ["no", "cancel", "n"]:
            p = st.session_state.pending_data
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["db_price"])
            st.session_state.chat_stage = None
            
            if action == "stock_insufficient":
                return f"❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                              if item['item_description'].lower() == p["product"].lower())
                return f"✅ Quantity increased by {p['qty']} at database price ₹{p['db_price']}. Total now {total_qty}"
            else:
                return f"✅ Added {p['qty']} {p['product']} at database price ₹{p['db_price']} to invoice"
        else:
            st.session_state.chat_stage = None
            return "Using database price."
    
    # ADD PRODUCT TO DB CONFIRMATION
    if st.session_state.chat_stage == "ADD":
        if text in ["yes", "ok", "okay", "confirm", "y"]:
            p = st.session_state.pending_data
            # Ask for initial stock
            if "stock" not in p:
                st.session_state.pending_data["stock"] = 0
                st.session_state.chat_stage = "ASK_INITIAL_STOCK"
                return f"How much initial stock for **{p['product']}**? (Enter 0 if no stock)"
        
        elif text in ["no", "cancel", "n"]:
            st.session_state.chat_stage = None
            return "❌ Product addition cancelled."
    
    # ASK INITIAL STOCK FOR NEW PRODUCT
    if st.session_state.chat_stage == "ASK_INITIAL_STOCK":
        stock = None
        numbers = re.findall(r'\d+', text)
        if numbers:
            stock = int(numbers[0])
        
        if stock is None:
            return "Please enter a valid stock quantity (numbers only)"
        
        p = st.session_state.pending_data
        success, message = add_product_to_db(p["product"], p["price"], stock)
        st.session_state.chat_stage = None
        
        if success:
            # Add the product to invoice with the requested quantity
            action, stock_info = add_or_update_invoice_item(p["product"], p["qty"], p["price"])
            
            if action == "stock_insufficient":
                return f"✅ **{p['product']}** added to database at ₹{p['price']} with {stock} stock\n\n❌ **Stock Insufficient!** Only {stock_info} units available for {p['product']}"
            elif action == "updated":
                total_qty = sum(item['qty'] for item in st.session_state.invoice 
                              if item['item_description'].lower() == p["product"].lower())
                return f"✅ **{p['product']}** added to database at ₹{p['price']} with {stock} stock\n✅ Quantity increased by {p['qty']}. Total now {total_qty}"
            else:
                return f"✅ **{p['product']}** added to database at ₹{p['price']} with {stock} stock\n✅ Added {p['qty']} {p['product']} to invoice"
        else:
            return f"❌ {message}"
    
    # ASK QUANTITY
    if st.session_state.chat_stage == "ASK_QTY":
        qty = None
        numbers = re.findall(r'\d+', text)
        if numbers:
            qty = int(numbers[0])
        
        if not qty:
            return "Please enter a valid quantity (numbers only)"
        
        st.session_state.pending_data["qty"] = qty
        st.session_state.chat_stage = "ASK_PRICE"
        return f"What should be the price for {qty} {st.session_state.pending_data['product']}?"
    
    # ASK PRICE
    if st.session_state.chat_stage == "ASK_PRICE":
        price = None
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            price = float(numbers[0])
        
        if not price:
            return "Please enter a valid price (numbers only)"
        
        p = st.session_state.pending_data
        product = p["product"]
        qty = p["qty"]
        
        exists, db_price, stock = check_product_exists(product)
        
        if not exists:
            st.session_state.pending_data = {"product": product, "qty": qty, "price": price}
            st.session_state.chat_stage = "ADD"
            return f"**{product}** not found in database. Add it with price ₹{price}?"
        else:
            if price != db_price:
                st.session_state.pending_data = {
                    "product": product,
                    "qty": qty,
                    "user_price": price,
                    "db_price": db_price
                }
                st.session_state.chat_stage = "CONFIRM_PRICE_CHANGE_FOR_ORDER"
                return f"Database shows **{product}** price as ₹{db_price}. You entered ₹{price}. Change price?"
            else:
                # Check stock availability
                if stock is not None and qty > stock:
                    # Add to stock alerts
                    st.session_state.stock_alert.append({
                        "product": product,
                        "requested": qty,
                        "available": stock,
                        "shortage": qty - stock
                    })
                    return f"❌ **Stock Insufficient!** Only {stock} units available for {product}"
                
                action, stock_info = add_or_update_invoice_item(product, qty, price)
                st.session_state.chat_stage = None
                
                if action == "stock_insufficient":
                    return f"❌ **Stock Insufficient!** Only {stock_info} units available for {product}"
                elif action == "updated":
                    total_qty = sum(item['qty'] for item in st.session_state.invoice 
                                  if item['item_description'].lower() == product.lower())
                    return f"✅ Quantity increased by {qty}. Total now {total_qty} at ₹{price} each"
                else:
                    return f"✅ Added {qty} {product} at ₹{price} to invoice"
    
    # CHECK IF INVOICE SETUP IS COMPLETE BEFORE ADDING PRODUCTS
    if not st.session_state.invoice_meta["project_id"]:
        product, qty, price, uom = extract_product_qty_price(user_text)
        if product:
            return "📋 Please start by typing 'generate invoice' to select project, party, and invoice type first."
        else:
            ai_response = get_ai_response(user_text, st.session_state.ai_context)
            st.session_state.ai_context.append({"role": "assistant", "content": ai_response})
            return ai_response
    
    # REGULAR PRODUCT ORDER (only if setup is complete)
    # REGULAR PRODUCT ORDER (only if setup is complete)
    product, qty, price, uom = extract_product_qty_price(user_text)

    if not product:
        product = smart_product_match(user_text)

    if not product:
        ai_response = get_ai_response(user_text, st.session_state.ai_context)
        st.session_state.ai_context.append({"role": "assistant", "content": ai_response})
        return ai_response

    # Clean product name
    product = re.sub(r'\s*(?:rs|₹|inr|\d+)$', '', product, flags=re.IGNORECASE).strip()

    exists, db_price, stock = check_product_exists_simple(product)

    # Convert price to float if it exists
    price_float = None
    if price is not None:
        try:
            price_float = float(price)
        except (ValueError, TypeError):
            price_float = None

    if not exists:
        if qty is None:
            st.session_state.chat_stage = "ASK_QTY"
            st.session_state.pending_data = {"product": product}
            return f"**{product}** not in database. How many?"
        
        if price_float is None:
            st.session_state.chat_stage = "ASK_PRICE"
            st.session_state.pending_data = {"product": product, "qty": qty}
            return f"Price for {qty} {product}?"
        
        st.session_state.pending_data = {"product": product, "qty": qty, "price": price_float}
        st.session_state.chat_stage = "ADD"
        return f"**{product}** not in database. Add it with price ₹{price_float}?"

    if qty is None:
        st.session_state.chat_stage = "ASK_QTY"
        st.session_state.pending_data = {"product": product}
        return f"How many **{product}**? (Database price: ₹{db_price}, Stock: {stock if stock is not None else 'N/A'})"

    if price_float is None:
        st.session_state.chat_stage = "ASK_PRICE"
        st.session_state.pending_data = {"product": product, "qty": qty}
        return f"Price for {qty} {product}? (Database price: ₹{db_price}, Stock: {stock if stock is not None else 'N/A'})"

    # Convert db_price to float for comparison
    db_price_float = None
    if db_price is not None:
        try:
            db_price_float = float(db_price)
        except (ValueError, TypeError):
            db_price_float = 0

    # PRICE COMPARISON LOGIC
    if price_float != db_price_float:
        # Calculate price difference percentage
        try:
            price_diff = ((price_float - db_price_float) / db_price_float) * 100 if db_price_float > 0 else 0
        except (ValueError, TypeError):
            price_diff = 0
        
        if price_float < db_price_float:
            # Lower price - ask for confirmation
            if price_diff < -10:  # More than 10% lower
                st.session_state.pending_data = {
                    "product": product,
                    "qty": qty,
                    "user_price": price_float,
                    "db_price": db_price_float,
                    "diff_percent": abs(price_diff)
                }
                st.session_state.chat_stage = "CONFIRM_LOW_PRICE"
                return f"⚠️ **Warning: Lower Price!**\nDatabase price: ₹{db_price_float}\nYour price: ₹{price_float}\n({abs(price_diff):.1f}% lower)\n\nProceed with lower price?"
            else:
                # Small difference, proceed automatically
                action, stock_info = add_or_update_invoice_item(product, qty, price_float, uom)
                
                if action == "stock_insufficient":
                    return f"❌ **Stock Insufficient!** Only {stock_info} units available for {product}"
                elif action == "updated":
                    total_qty = sum(item['qty'] for item in st.session_state.invoice 
                                if item['item_description'].lower() == product.lower())
                    return f"✅ Added {qty} {product} at **slightly lower price ₹{price_float}** (DB: ₹{db_price_float}). Total now {total_qty}"
                else:
                    return f"✅ Added {qty} {product} at **slightly lower price ₹{price_float}** (DB: ₹{db_price_float})"
        
        else:  # price_float > db_price_float
            # Higher price - ask for confirmation and option to update DB
            st.session_state.pending_data = {
                "product": product,
                "qty": qty,
                "user_price": price_float,
                "db_price": db_price_float,
                "diff_percent": price_diff,
                "update_db": False
            }
            st.session_state.chat_stage = "CONFIRM_HIGH_PRICE"
            return f"💰 **Higher Price Detected!**\nDatabase price: ₹{db_price_float}\nYour price: ₹{price_float}\n({price_diff:.1f}% higher)\n\nDo you want to:\n1. Use higher price? (Type 'yes')\n2. Use database price? (Type 'no')\n3. Update database to new price? (Type 'update')"

    # If prices are equal or db_price_float is None, proceed with adding item
    # Check stock before adding
    if stock is not None and qty > stock:
        # Add to stock alerts
        st.session_state.stock_alert.append({
            "product": product,
            "requested": qty,
            "available": stock,
            "shortage": qty - stock
        })
        return f"❌ **Stock Insufficient!** Only {stock} units available for {product}"

    action, stock_info = add_or_update_invoice_item(product, qty, price_float, uom)

    if action == "stock_insufficient":
        return f"❌ **Stock Insufficient!** Only {stock_info} units available for {product}"
    elif action == "updated":
        total_qty = sum(item['qty'] for item in st.session_state.invoice 
                    if item['item_description'].lower() == product.lower())
        return f"✅ Quantity increased by {qty}. Total now {total_qty} at ₹{price_float} each"
    else:
        return f"✅ Added {qty} {product} at ₹{price_float} to invoice"

# =========================
# MAIN UI
# =========================
st.title("💬 CRM GST Invoice Chatbot")

# Display stock alerts if any
if st.session_state.stock_alert:
    with st.expander("⚠️ Stock Alerts", expanded=True):
        for alert in st.session_state.stock_alert:
            st.warning(f"**{alert['product']}**: Requested {alert['requested']}, Available {alert['available']}, Shortage {alert['shortage']}")

# Display current selection status with GST info
if st.session_state.invoice_meta["project_name"] or st.session_state.invoice_meta["party_name"]:
    cols = st.columns(4)
    with cols[0]:
        if st.session_state.invoice_meta["project_name"]:
            st.info(f"**Project:** {st.session_state.invoice_meta['project_name']}")
    with cols[1]:
        if st.session_state.invoice_meta["party_name"]:
            st.info(f"**Party:** {st.session_state.invoice_meta['party_name']}")
    with cols[2]:
        if st.session_state.invoice_meta["invoice_type"]:
            st.info(f"**Type:** {st.session_state.invoice_meta['invoice_type']}")
    with cols[3]:
        if st.session_state.invoice_meta["party_pincode"]:
            gst_info = get_gst_rate_from_pincode(st.session_state.invoice_meta["party_pincode"])
            st.info(f"**GST:** {gst_info['type']}")

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    reply = chat_engine(user_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

def show_price_comparison(product_name, user_price=None):
    """Show price comparison between user price and database price"""
    exists, db_price, stock = check_product_exists(product_name)
    
    if not exists or db_price is None:
        return None
    
    if user_price is None:
        return f"**Database Price:** ₹{db_price:,.2f}"
    
    user_price = float(user_price)
    price_diff = ((user_price - db_price) / db_price) * 100
    
    if user_price == db_price:
        return f"✅ **Price Match:** ₹{user_price:,.2f} (Same as database)"
    
    elif user_price < db_price:
        if price_diff < -10:
            return f"⚠️ **Lower Price:** ₹{user_price:,.2f} (Database: ₹{db_price:,.2f}, {abs(price_diff):.1f}% lower)"
        else:
            return f"📉 **Slightly Lower:** ₹{user_price:,.2f} (Database: ₹{db_price:,.2f}, {abs(price_diff):.1f}% lower)"
    
    else:  # user_price > db_price
        return f"📈 **Higher Price:** ₹{user_price:,.2f} (Database: ₹{db_price:,.2f}, {price_diff:.1f}% higher)"

# =========================
# DISPLAY OLD INVOICE
# =========================
if st.session_state.viewing_old_invoice and st.session_state.old_invoice_data:
    st.markdown("---")
    invoice_no = st.session_state.old_invoice_data['header']['invoice_no']
    st.subheader(f"📋 Invoice #{invoice_no}")
    
    # Show format info if it follows new pattern
    if invoice_no.startswith("ICE/"):
        st.info(f"**Format:** `{invoice_no}`")
    
    # Display invoice header info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Project", st.session_state.old_invoice_data['header']['project_name'])
    with col2:
        st.metric("Party", st.session_state.old_invoice_data['header']['party_name'])
    with col3:
        st.metric("Date", str(st.session_state.old_invoice_data['header']['invoice_date']))
    
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Type", st.session_state.old_invoice_data['header']['invoice_type'])
    with col5:
        st.metric("Subtotal", f"₹{st.session_state.old_invoice_data['header']['subtotal']:,.2f}")
    with col6:
        st.metric("Grand Total", f"₹{st.session_state.old_invoice_data['header']['grand_total']:,.2f}")
    
        # Display invoice items with all details
    st.subheader("📦 Invoice Items")
    items_data = []
    for item in st.session_state.old_invoice_data['items']:
        items_data.append({
            "No.": len(items_data) + 1,
            "Description": item['item_description'],
            "UOM": item.get('uom', ''),
            "Quantity": item['quantity'],
            "Rate": f"₹{item['unit_price']:,.2f}",
            "Discount": f"₹{item.get('discount', 0):,.2f}" if item.get('discount', 0) > 0 else "-",
            "Tax %": f"{item.get('tax_percentage', 0):.1f}%" if item.get('tax_percentage', 0) > 0 else "-",
            "Tax Amount": f"₹{item.get('tax_amount', 0):,.2f}" if item.get('tax_amount', 0) > 0 else "-",
            "Total": f"₹{item['total_price']:,.2f}"
        })
    
    if items_data:
        df_items = pd.DataFrame(items_data)
        st.dataframe(df_items, use_container_width=True, hide_index=False)
    else:
        st.warning("No items found for this invoice")
    
    # Display Tax breakdown
    st.subheader("💰 Tax Calculation")
    
    # Get tax amount from database
    tax_amount = st.session_state.old_invoice_data['header']['tax']
    subtotal = st.session_state.old_invoice_data['header']['subtotal']
    discount = st.session_state.old_invoice_data['header']['discount']
    grand_total = st.session_state.old_invoice_data['header']['grand_total']
    
    col7, col8, col9, col10 = st.columns(4)
    with col7:
        st.metric("Subtotal", f"₹{subtotal:,.2f}")
    with col8:
        st.metric("Discount", f"₹{discount:,.2f}")
    with col9:
        st.metric("Tax", f"₹{tax_amount:,.2f}")
    with col10:
        st.metric("Grand Total", f"₹{grand_total:,.2f}")
    
    st.divider()
    
    # Display party info
    if st.session_state.old_invoice_data['header']['party_address']:
        with st.expander("📋 Party Details"):
            st.write(f"**Address:** {st.session_state.old_invoice_data['header']['party_address']}")
            if st.session_state.old_invoice_data['header']['party_pincode']:
                st.write(f"**Pincode:** {st.session_state.old_invoice_data['header']['party_pincode']}")
            if st.session_state.old_invoice_data['header']['party_gst']:
                st.write(f"**GST:** {st.session_state.old_invoice_data['header']['party_gst']}")
    
        # Add download and close buttons
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        # Download as PDF button
        if st.button("📥 Download Invoice as PDF", type="primary", use_container_width=True):
            # Create a PDF of the invoice
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, mm
            import io
            
            # Create a buffer for the PDF
            buffer = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                alignment=1,  # Center aligned
                spaceAfter=12
            )
            elements.append(Paragraph("TAX INVOICE", title_style))
            
            # Invoice details in a table
            invoice_data = [
                ["Invoice No:", invoice_no],
                ["Date:", str(st.session_state.old_invoice_data['header']['invoice_date'])],
                ["Type:", st.session_state.old_invoice_data['header']['invoice_type']],
                ["Status:", st.session_state.old_invoice_data['header']['status'].upper()]
            ]
            
            invoice_table = Table(invoice_data, colWidths=[1.5*inch, 3*inch])
            invoice_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(invoice_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # From and To sections side by side
            from_to_data = []
            
            # From section
            from_section = [
                ["<b>From:</b>"],
                ["Company Name"],
                ["Address Line 1"],
                ["Address Line 2"],
                ["GSTIN: XXXXXXXX"],
                ["State: Tamil Nadu"]
            ]
            
            # To section
            to_section = [
                ["<b>To:</b>"],
                [st.session_state.old_invoice_data['header']['party_name']],
                [st.session_state.old_invoice_data['header'].get('party_address', '')],
                [""],
                [f"GSTIN: {st.session_state.old_invoice_data['header'].get('party_gst', '')}"],
                [f"State: {st.session_state.old_invoice_data['header'].get('party_pincode', '')}"]
            ]
            
            # Combine into a table
            combined_data = []
            for i in range(max(len(from_section), len(to_section))):
                row = []
                if i < len(from_section):
                    row.append(Paragraph(from_section[i][0], styles["Normal"]))
                else:
                    row.append("")
                
                if i < len(to_section):
                    row.append(Paragraph(to_section[i][0], styles["Normal"]))
                else:
                    row.append("")
                combined_data.append(row)
            
            from_to_table = Table(combined_data, colWidths=[2.5*inch, 3*inch])
            from_to_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(from_to_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Items table header
            items_header = ["S.No", "Description", "UOM", "Quantity", "Rate (₹)", "Discount (₹)", "Tax %", "Tax Amt (₹)", "Amount (₹)"]
            
            # Items data
            items_data = []
            for i, item in enumerate(st.session_state.old_invoice_data['items'], 1):
                items_data.append([
                    str(i),
                    item['item_description'][:50],  # Limit description length
                    item.get('uom', ''),
                    f"{item['quantity']:,.2f}",
                    f"{item['unit_price']:,.2f}",
                    f"{item.get('discount', 0):,.2f}",
                    f"{item.get('tax_percentage', 0):.1f}%" if item.get('tax_percentage', 0) > 0 else "-",
                    f"{item.get('tax_amount', 0):,.2f}",
                    f"{item['total_price']:,.2f}"
                ])
            
            # Combine header and data
            table_data = [items_header] + items_data
            
            # Create items table
            items_table = Table(table_data, colWidths=[0.4*inch, 2*inch, 0.5*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.6*inch, 0.8*inch, 0.8*inch])
            items_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Description left aligned
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
                ('FONTSIZE', (1, 1), (1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Totals section
            header = st.session_state.old_invoice_data['header']
            totals_data = [
                ["", "", "", "", "", "Subtotal:", f"₹{header['subtotal']:,.2f}"],
                ["", "", "", "", "", "Discount:", f"₹{header['discount']:,.2f}"],
                ["", "", "", "", "", "Tax:", f"₹{header['tax']:,.2f}"],
                ["", "", "", "", "", "<b>Grand Total:</b>", f"<b>₹{header['grand_total']:,.2f}</b>"]
            ]
            
            totals_table = Table(totals_data, colWidths=[0.4*inch, 2*inch, 0.5*inch, 0.6*inch, 0.8*inch, 1.5*inch, 1*inch])
            totals_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
                ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
                ('FONTNAME', (5, -1), (6, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (5, -1), (6, -1), 12),
            ]))
            elements.append(totals_table)
            
            # Footer
            elements.append(Spacer(1, 0.5*inch))
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=8,
                alignment=1,
                textColor=colors.grey
            )
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", footer_style))
            elements.append(Paragraph("Thank you for your business!", footer_style))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF data
            buffer.seek(0)
            pdf_data = buffer.getvalue()
            
            # Download button
            st.download_button(
                label="⬇️ Click to Download PDF",
                data=pdf_data,
                file_name=f"Invoice_{invoice_no}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.success(f"✅ PDF generated for invoice {invoice_no}")
    
    with col_d2:
        # Close button
        if st.button("❌ Close Invoice", type="secondary", use_container_width=True):
            st.session_state.viewing_old_invoice = False
            st.session_state.old_invoice_data = None
            st.rerun()


    # CSV Download Option
    st.divider()
    st.subheader("📊 Export Options")


    # Create CSV content
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Header section
    csv_writer.writerow(["INVOICE DETAILS"])
    csv_writer.writerow(["Invoice No:", invoice_no])
    csv_writer.writerow(["Date:", str(st.session_state.old_invoice_data['header']['invoice_date'])])
    csv_writer.writerow(["Project:", st.session_state.old_invoice_data['header']['project_name']])
    csv_writer.writerow(["Party:", st.session_state.old_invoice_data['header']['party_name']])
    csv_writer.writerow(["Type:", st.session_state.old_invoice_data['header']['invoice_type']])
    csv_writer.writerow(["Address:", st.session_state.old_invoice_data['header'].get('party_address', 'N/A')])
    csv_writer.writerow(["GST:", st.session_state.old_invoice_data['header'].get('party_gst', 'N/A')])
    csv_writer.writerow(["Status:", st.session_state.old_invoice_data['header']['status']])
    csv_writer.writerow([])

    # Items header
    csv_writer.writerow(["ITEMS"])
    csv_writer.writerow(["S.No", "Description", "UOM", "Quantity", "Rate (₹)", "Discount (₹)", "Tax %", "Tax Amount (₹)", "Total (₹)"])

    # Items data
    for i, item in enumerate(st.session_state.old_invoice_data['items'], 1):
        csv_writer.writerow([
            i,
            item['item_description'],
            item.get('uom', ''),
            item['quantity'],
            item['unit_price'],
            item.get('discount', 0),
            item.get('tax_percentage', 0),
            item.get('tax_amount', 0),
            item['total_price']
        ])

    csv_writer.writerow([])

    # Totals
    header = st.session_state.old_invoice_data['header']
    csv_writer.writerow(["SUMMARY"])
    csv_writer.writerow(["", "", "", "", "", "Subtotal:", header['subtotal']])
    csv_writer.writerow(["", "", "", "", "", "Discount:", header['discount']])
    csv_writer.writerow(["", "", "", "", "", "Tax:", header['tax']])
    csv_writer.writerow(["", "", "", "", "", "Grand Total:", header['grand_total']])
    csv_writer.writerow([])
    csv_writer.writerow(["Generated on:", datetime.now().strftime("%d-%m-%Y %H:%M:%S")])

    csv_str = csv_buffer.getvalue()

    # Download CSV button
    st.download_button(
        label="📥 Download as CSV",
        data=csv_str,
        file_name=f"Invoice_{invoice_no}_detailed.csv",
        mime="text/csv",
        use_container_width=True
    )

# =========================
# INVOICE VIEW WITH GST CALCULATION
# =========================
elif st.session_state.invoice:
    st.markdown("---")
    st.subheader("🧾 Current Invoice")
    
    # Show invoice number if generated
    if st.session_state.invoice_meta.get("invoice_no"):
        st.success(f"**Invoice Number:** {st.session_state.invoice_meta['invoice_no']}")
    
    # Calculate totals
    subtotal = 0
    for item in st.session_state.invoice:
        qty = item.get("qty")
        price = item.get("supply_rate")
        if qty is not None and price is not None:
            try:
                subtotal += float(qty) * float(price)
            except (ValueError, TypeError):
                continue
    
    pincode = st.session_state.invoice_meta["party_pincode"]
    gst_calc = calculate_gst_breakdown(subtotal, pincode)
    
    
    # Create dataframe with all information
    invoice_data = []
    for item in st.session_state.invoice:
        row = {
            "Product": item["item_description"],
            "UOM": item.get("uom", "nos"),
            "Quantity": item["qty"],
            "Price": item["supply_rate"],
            "Total": item["qty"] * item["supply_rate"]
        }
        
        # Add stock information
        stock = get_product_stock(item["item_description"])
        if stock is not None:
            row["Available Stock"] = stock
            if stock < item["qty"]:
                row["Stock Status"] = "⚠️ Insufficient"
            else:
                row["Stock Status"] = "✅ Sufficient"
        
        # Add meta info if available
        if "project" in item:
            row["Project"] = item["project"]
        elif st.session_state.invoice_meta["project_name"]:
            row["Project"] = st.session_state.invoice_meta["project_name"]
            
        if "party" in item:
            row["Party"] = item["party"]
        elif st.session_state.invoice_meta["party_name"]:
            row["Party"] = st.session_state.invoice_meta["party_name"]
            
        if "invoice_type" in item:
            row["Invoice Type"] = item["invoice_type"]
        elif st.session_state.invoice_meta["invoice_type"]:
            row["Invoice Type"] = st.session_state.invoice_meta["invoice_type"]
        
        invoice_data.append(row)
    
    df = pd.DataFrame(invoice_data)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display items table with stock info
        st.write("**Invoice Items:**")
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Project": st.column_config.TextColumn("Project", disabled=True),
                "Party": st.column_config.TextColumn("Party", disabled=True),
                "Invoice Type": st.column_config.TextColumn("Type", disabled=True),
                "Product": st.column_config.TextColumn("Product", disabled=True),
                "UOM": st.column_config.TextColumn("UOM", disabled=True),
                "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, disabled=False),
                "Price": st.column_config.NumberColumn("Price", format="₹%.2f", min_value=0.0, disabled=False),
                "Total": st.column_config.NumberColumn("Total", format="₹%.2f", disabled=True),
                "Available Stock": st.column_config.NumberColumn("Available Stock", disabled=True),
                "Stock Status": st.column_config.TextColumn("Stock Status", disabled=True)
            },
            num_rows="dynamic",
            key="invoice_editor"
        )
        
        # Update if edited
        if not df.equals(edited_df):
            updated_invoice = []
            for _, row in edited_df.iterrows():
                item = {
                    "item_description": row["Product"],
                    "qty": row["Quantity"],
                    "supply_rate": row["Price"]
                }
                
                # Add back meta info
                if "Project" in row:
                    item["project"] = row["Project"]
                if "Party" in row:
                    item["party"] = row["Party"]
                if "Invoice Type" in row:
                    item["invoice_type"] = row["Invoice Type"]
                
                updated_invoice.append(item)
            
            st.session_state.invoice = updated_invoice
            st.rerun()
    
    with col2:
        # Display invoice summary with new format
        st.subheader("📋 Invoice Summary")
        
        # Show invoice number preview if not generated yet
        if not st.session_state.invoice_meta.get("invoice_no"):
            # Preview what the invoice number will look like
            invoice_type = st.session_state.invoice_meta["invoice_type"]
            
            # Map invoice type to code
            type_mapping = {
                "Credit Note": "CN",
                "Debit Note": "DN",
                "Delivery Challan": "DCH",
                "Purchase Invoice": "PI",
                "Purchase Order": "PO",
                "Sales Invoice": "INV",
                "Tax Invoice": "INV",
                "Proforma Invoice": "PINV"
            }
            
            type_code = type_mapping.get(invoice_type, "INV")
            
            # Get current financial year
            current_year = datetime.now().year
            if datetime.now().month >= 4:
                fin_year = f"{current_year}-{current_year+1}"
            else:
                fin_year = f"{current_year-1}-{current_year}"
            
            # Try to get next sequence
            try:
                with ENGINE.connect() as conn:
                    query = text("""
                        SELECT invoice_sequence 
                        FROM invoice_settings 
                        WHERE invoice_type_code = :type_code
                        LIMIT 1
                    """)
                    result = conn.execute(query, {"type_code": type_code})
                    row = result.fetchone()
                    if row:
                        next_seq = row[0]
                    else:
                        next_seq = 1
                
                preview_no = f"ICE/{fin_year}/{type_code}/{str(next_seq).zfill(4)}"
                st.info(f"**Next Invoice:**\n`{preview_no}`")
            except:
                st.info(f"**Format:** ICE/{fin_year}/{type_code}/[0001+]")
        
        st.metric("Subtotal", f"₹{subtotal:,.2f}")
        
        if gst_calc["gst_type"] == "CGST+SGST":
            st.metric("CGST (9%)", f"₹{gst_calc['cgst_amount']:,.2f}")
            st.metric("SGST (9%)", f"₹{gst_calc['sgst_amount']:,.2f}")
        else:
            st.metric("IGST (18%)", f"₹{gst_calc['igst_amount']:,.2f}")
        
        st.divider()
        st.metric("Total GST", f"₹{gst_calc['total_gst']:,.2f}", 
                  delta=f"{gst_calc['gst_type']}")
        st.metric("Grand Total", f"₹{gst_calc['grand_total']:,.2f}", 
                  delta_color="off")
        
        # Display party info
        if st.session_state.invoice_meta["party_address"]:
            with st.expander("📋 Party Details"):
                st.write(f"**Address:** {st.session_state.invoice_meta['party_address']}")
                if st.session_state.invoice_meta["party_pincode"]:
                    st.write(f"**Pincode:** {st.session_state.invoice_meta['party_pincode']}")
                if st.session_state.invoice_meta["party_gst"]:
                    st.write(f"**GST:** {st.session_state.invoice_meta['party_gst']}")
        
        # Stock summary
        st.subheader("📦 Stock Summary")
        for item in st.session_state.invoice:
            stock = get_product_stock(item["item_description"])
            if stock is not None:
                if stock >= item["qty"]:
                    st.success(f"{item['item_description']}: {stock} → {stock - item['qty']} (after invoice)")
                else:
                    st.error(f"{item['item_description']}: Only {stock} available, need {item['qty']}")
        
        # Generate Invoice Button
        if st.button("📤 Generate Final Invoice", type="primary", use_container_width=True):
            success, message = save_invoice_to_db()
            if success:
                st.success("✅ Invoice generated successfully!")
                st.info(message)
                # Show the generated invoice number
                if st.session_state.invoice_meta.get("invoice_no"):
                    st.balloons()
                    st.subheader(f"🎉 Invoice Generated: {st.session_state.invoice_meta['invoice_no']}")
                
                # Clear invoice after generation
                st.session_state.invoice = []
                st.session_state.stock_alert = []
                st.rerun()
            else:
                st.error(f"❌ {message}")

# Initial greeting
if not st.session_state.messages:
    with st.chat_message("assistant"):
        greeting = "👋 **Hi! I'm your Invoice Assistant with GST Calculation & Stock Management**\n\n"
        
        # Add price comparison examples
        greeting += "**✨ Smart Price Detection:**\n"
        greeting += "• If you say 'pen is ₹50 only' - I'll check if database price is different\n"
        greeting += "• If you say 'pen rate is cheaper by ₹10' - I'll compare with database\n"
        greeting += "• If you say 'old price was ₹60, new is ₹70' - I'll alert you\n\n"
        
        # Add update commands
        greeting += "**🔄 Update Commands:**\n"
        greeting += "• '**update pen quantity to 10**' - Updates invoice & database\n"
        greeting += "• '**change screwdriver price to ₹50**' - Updates invoice & database\n"
        greeting += "• '**set hammer stock to 20**' - Updates database stock\n"
        greeting += "• '**update notebook rate as ₹25**' - Updates price in both\n\n"
        
        greeting += "**Examples:**\n"
        greeting += "• 'Pen price is ₹45 only' → Checks database price\n"
        greeting += "• 'Need 10 notebooks at ₹100 each' → Compares with DB\n"
        greeting += "• 'Screwdriver cheaper by ₹20' → Shows difference\n"
        greeting += "• 'Hammer more expensive now ₹500' → Alerts price increase\n"
        greeting += "• 'Update pen quantity to 15' → Updates invoice and database\n"
        greeting += "• 'Change screwdriver price to ₹75' → Updates price in both\n\n"
        
        greeting += "**To create an invoice:**\n"
        greeting += "1. Type '**generate invoice**'\n"
        greeting += "2. Select project from database\n" 
        greeting += "3. Select party (with address, pincode, GST from database)\n"
        greeting += "4. Select invoice type\n"
        greeting += "5. Add products (e.g., 'i need 10 pen for 50 rs')\n"
        greeting += "6. Click 'Generate Final Invoice' button\n\n"
        greeting += "**To view invoices:**\n"
        greeting += "• Type '**list invoices**' to see all invoices\n"
        greeting += "• Type '**view invoice ICE/25-26/INV/0018**' (with the complete invoice number)\n\n"
        greeting += "**✨ Stock Management:**\n"
        greeting += "• Automatically checks stock availability\n"
        greeting += "• Updates stock after invoice generation\n"
        greeting += "• Alerts for insufficient stock\n\n"
        greeting += "**Stock Commands:**\n"
        greeting += "• '**check stock pen**' - Check available stock\n"
        greeting += "• '**add stock pen by 10**' - Increase stock\n"
        greeting += "• '**set stock pen to 50**' - Set specific stock quantity\n\n"
        greeting += "**Other Commands:**\n"
        greeting += "• Change prices: '**change pen price to ₹10**'\n"
        greeting += "• Debug: '**debug tables**', '**debug table parties**'\n"
        greeting += "• Search: '**search invoices PO/020**'\n"
        greeting += "• Type '**view invoice ICE/25-26/INV/0018**' (with the complete invoice number)\n\n"
        greeting += "**New Invoice Format:**\n"
        greeting += "• ICE/25-26/INV/0001 (Sales Invoice)\n"
        greeting += "• ICE/25-26/PO/0001 (Purchase Order)\n"
        greeting += "• ICE/25-26/CN/0001 (Credit Note)\n"
        greeting += "• ICE/25-26/DN/0001 (Debit Note)\n"
        greeting += "• ICE/25-26/DCH/0001 (Delivery Challan)\n"
        greeting += "• ICE/25-26/PI/0001 (Purchase Invoice)\n\n"
        greeting += "**New Invoice Format Examples:**\n"
        greeting += "• `ICE/25-26/INV/0001` (Sales Invoice)\n"
        greeting += "• `ICE/25-26/PO/0001` (Purchase Order)\n"
        greeting += "• `ICE/25-26/CN/0001` (Credit Note)\n"
        greeting += "• `ICE/25-26/DN/0001` (Debit Note)\n"
        greeting += "• `ICE/25-26/DCH/0001` (Delivery Challan)\n"
        greeting += "• `ICE/25-26/PI/0001` (Purchase Invoice)\n\n"
        greeting += "**To create an invoice:**\n"
        greeting += "**🔄 Update Commands:**\n"
        greeting += "• '**increase pen by 5**' - Increase quantity in invoice\n"
        greeting += "• '**delete pen row**' - Remove item from invoice\n"
        greeting += "• '**update pen quantity to 10**' - Updates invoice & database\n"
        greeting += "• '**change screwdriver price to ₹50**' - Updates invoice & database\n"
        greeting += "• '**set hammer stock to 20**' - Updates database stock\n"
        greeting += "• '**update notebook rate as ₹25**' - Updates price in both\n\n"
        greeting += "**Examples:**\n"
        greeting += "• 'Pen price is ₹45 only' → Checks database price\n"
        greeting += "• 'Need 10 notebooks at ₹100 each' → Compares with DB\n"
        greeting += "• 'Screwdriver cheaper by ₹20' → Shows difference\n"
        greeting += "• 'Hammer more expensive now ₹500' → Alerts price increase\n"
        greeting += "• 'Need 10kg cement for ₹500' → Extracts UOM (kg)\n"
        greeting += "• 'Add 5 boxes of screws at ₹200' → Extracts UOM (boxes)\n"
        greeting += "• 'Update pen quantity to 15' → Updates invoice and database\n"
        greeting += "• 'Change screwdriver price to ₹75' → Updates price in both\n\n"
        
        st.markdown(greeting)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": greeting
        })






















