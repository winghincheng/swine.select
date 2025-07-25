
import streamlit as st
import pandas as pd
from io import BytesIO

# --- App State ---
if "data" not in st.session_state:
    st.session_state.data = []

# --- Helper Functions ---
def generate_tag_id(breed, swine_id):
    prefix_map = {"YG": "KPAY", "LG": "KPAL", "DG": "KPAD", "YB": "KPAY", "LB": "KPAL", "DB": "KPAD"}
    return f"{prefix_map.get(breed, 'KPA')} {swine_id}"

def to_excel(df, pivot):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Swine Selection', index=False)
        pivot.to_excel(writer, sheet_name='Pivot Table')
    output.seek(0)
    return output

# --- UI ---
st.title("Swine Selection Recorder")

with st.form("entry_form"):
    swine_id = st.text_input("ID (≤10 digits)", max_chars=10, help="Numeric tag ID")
    location = st.text_input("Pen Location", value=st.session_state.get("last_location", ""), max_chars=10)
    breed = st.selectbox("Breed", ["YG", "LG", "DG", "YB", "LB", "DB"],
                         index=0 if "last_breed" not in st.session_state else ["YG", "LG", "DG", "YB", "LB", "DB"].index(st.session_state.last_breed))
    bt = st.selectbox("BT", ["", "bt"], index=0 if "last_bt" not in st.session_state else ["", "bt"].index(st.session_state.last_bt))
    comment = st.text_input("Comment (max 100 characters)", max_chars=100)
    submitted = st.form_submit_button("Add Entry")

if submitted:
    if not swine_id.isdigit() or len(swine_id) > 10:
        st.error("ID must be numeric and up to 10 digits.")
    elif not location:
        st.error("Location is required.")
    else:
        tag_id = generate_tag_id(breed, swine_id)
        is_duplicate = any(row[1] == tag_id and row[0] == location for row in st.session_state.data)
        if is_duplicate:
            st.warning(f"Duplicate entry for Tag ID {tag_id} at {location}. Entry not added.")
        else:
            st.session_state.data.append([location, tag_id, swine_id, breed, bt if bt == "bt" else "", comment])
            st.session_state.last_location = location
            st.session_state.last_breed = breed
            st.session_state.last_bt = bt
            st.success(f"Saved: {tag_id}")

# --- Search and Highlight ---
if st.session_state.data:
    search_input = st.text_input("🔍 Search by Tag ID")
    df = pd.DataFrame(st.session_state.data, columns=["Location", "Tag ID", "ID", "Breed", "BT", "Comment"])
    if search_input:
        if search_input in df["Tag ID"].values:
            df["_highlight"] = df["Tag ID"].apply(lambda x: "background-color: yellow" if x == search_input else "")
            st.success(f"Found entry for {search_input}")
        else:
            df["_highlight"] = ""
            st.error("No matching Tag ID found.")
    else:
        df["_highlight"] = ""

    def highlight_row(row):
        return [row["_highlight"]]*6

    st.dataframe(df.drop(columns=["_highlight"]).style.apply(highlight_row, axis=1))

    # --- Export Section ---
    pivot = df.drop(columns=["_highlight"]).pivot_table(index="Location", columns="Breed", aggfunc="size", fill_value=0)
    xlsx_file = to_excel(df.drop(columns=["_highlight"]), pivot)
    st.download_button("📥 Export to Excel", data=xlsx_file, file_name="swine_selection.xlsx")
