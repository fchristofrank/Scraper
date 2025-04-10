## 🥗 Nutrition Data Consistency Checker

### 📌 Objective  
Verify whether the nutritional data from **Target's backend** matches the data in the **Grocery Database**.

---

### ✅ Solution Overview  

1. **Fetch Data from Target Backend**  
   - Retrieve all nutritional fields from Target’s API.

2. **Compare Against Grocery DB**  
   - For each field:
     - Check if it exists in the Grocery DB.
     - If it does, compare the values.
     - Flag discrepancies where values differ.

3. **Whole Foods & Walmart Support**  
   - These retailers do not provide APIs for nutritional data.
   - Instead, we **scrape nutritional data from their product pages' HTML** using `BeautifulSoup`. [Not yet done, prev researcher (Babak?) codes can be slightly reused)

---

### ⚠️ Challenge  
The **Discovery Servers** currently do **not allow outbound network traffic** to access the Grocery DB directly.

---

### 🛠️ Workaround  
- Generated a **CSV dump** of the Grocery DB.  
- Updated the logic in `DiscoveryVersion.py` to read data from the CSV file instead of making live DB calls.
