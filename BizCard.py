import streamlit as st
import streamlit_option_menu as option_menu
import pandas as pd
import easyocr
import mysql.connector
import cv2
import os
from matplotlib import pyplot as plt
import re
from PIL import Image
from time import sleep
from stqdm import stqdm
from io import BytesIO

reader = easyocr.Reader(['en'], gpu = False)

#SQL connect Module
def mysql_connect():
    return mysql.connector.connect(host='localhost', user='root', password='12345', database='BizCard')

def create_mysql_tables():
    connection = mysql_connect()
    mycursor = connection.cursor()
    
    create_query  = '''CREATE TABLE IF NOT EXISTS card_data
                (card_holder_name TEXT,
                designation TEXT,
                company_name TEXT,
                mobile_no VARCHAR(50),
                website TEXT,
                mail_id TEXT,
                door_no VARCHAR(50), 
                city TEXT,
                state TEXT,
                pincode VARCHAR(10),
                image LONGBLOB
                )'''
    mycursor.execute(create_query)
    connection.commit()

def image_ext(image):
    results = reader.readtext(image)

    img_1 = cv2.imread(image)
    font = cv2.FONT_HERSHEY_SIMPLEX
    plt.axis("off")

    for i in results:
        top_left = tuple([int(val) for val in i[0][0]])
        bottom_right = tuple([int(val) for val in i[0][2]])
        text = i[1]
        img_1 = cv2.rectangle(img_1,top_left,bottom_right,(0,255,0),3)
        img_1 = cv2.putText(img_1,text,top_left,font, 1,(225,0,0),2,cv2.LINE_AA)  
    # Convert the image from OpenCV format to PIL format
    img_pil = Image.fromarray(cv2.cvtColor(img_1, cv2.COLOR_BGR2RGB))
    # Display the resulting image using Streamlit
    st.image(img_pil, caption='Processed Image With Marking', use_column_width=True)
    
# Set page configuration
st.set_page_config(layout="wide")

# Create dropdown menu in the sidebar
with st.sidebar:
    Select = st.selectbox("Main Menu", ["About", "Sample process", "Data Extract", "View Data", "Make change","Remove Data"])

# Main content based on the selection
if Select == "About":
    st.subheader("About the Application")
    st.write(" Users can save the information extracted from the card image using easy OCR. The information can be uploaded into a database (MySQL) after alterations that supports multiple entries. ")
    st.subheader("What is Easy OCR?")
    st.write("Easy OCR is user-friendly Optical Character Recognition (OCR) technology, converting documents like scanned paper, PDFs, or digital camera images into editable and searchable data. A variety of OCR solutions, including open-source libraries, commercial software, and cloud-based services, are available. These tools are versatile, used for extracting text from images, recognizing printed or handwritten text, and making scanned documents editable.")

# Sample process how the data extract is woking
elif Select == "Sample process":
    st.header("Sample Extract Data")
    
    coll1,coll2 = st.columns(2)
    with coll1:
    # Create an upload box
        uploaded_file = st.file_uploader("Upload a image file", type=['png','jpg','jpeg'])
        
    image_path = None  # Define image_path outside the if block
   
    if uploaded_file is not None:
        coll1, coll2 = st.columns(2, gap="large")
        with coll1:
        # Check if a file was upload
            if uploaded_file is not None:  
                if uploaded_file.type.startswith('image'):
                    st.image(uploaded_file,caption='Upload Image')
                else:
                    st.write("Upload file is not an image")
        
        with coll2:
            image_path = os.getcwd() +"\\" + "Sample pic" + "\\" + uploaded_file.name
            extension = image_ext(image_path)  
    
    coll1,coll2 = st.columns(2)
    with coll1:
        if image_path:
            with stqdm(total=1, desc="Processing Image") as progress_bar: 
                results = reader.readtext(image_path)
                img_df = pd.DataFrame(results, columns=['bbox','text','conf'])
                st.write(img_df)
                progress_bar.update(1)
        
elif Select == "Data Extract":
    st.header("Extract Data for Upload in SQL")
    
    coll1,coll2 = st.columns(2)
    with coll1:
        uploaded_file = st.file_uploader("Upload a image file", type=['png','jpg','jpeg'])
                
    if uploaded_file != None:
        coll1,coll2 = st.columns(2, gap= "Large")
        with coll1:
            img = uploaded_file.read()
            st.image(img, caption="Image has been uploaded successfully",width=500)
            
        with coll2:
            image_path = os.getcwd() + "\\" + "Sample pic" + "\\"+ uploaded_file.name
            extension = image_ext(image_path)
            
            data_path = os.getcwd() + "\\" + "Sample pic" + "\\"+ uploaded_file.name
            result = reader.readtext(data_path, detail=0, paragraph=False)
            
            def img_to_binary(file):
            # Convert image data to binary format
                with open(file, 'rb') as file:
                    binaryData = file.read()
                return binaryData
            
            # Initialize dictionary to store card data
            card_data = {
                    "card_holder_name": [],
                    "designation": [],
                    "company_name": [],
                    "mobile_no": [],
                    "website": [],
                    "mail_id": [],
                    "door_no": [],
                    "city": [],
                    "state": [],
                    "pincode": [],
                    "image": img_to_binary(data_path)
                }
            
            def card_data_ext(text): 
            # Loop through each item in the text
                for value, i in enumerate(text): 
                    # Store card holder name
                    if value == 0:
                        card_data["card_holder_name"].append(i)
                    # Store designation
                    elif value == 1:
                        card_data["designation"].append(i)
                    # Store company name (assumed to be the last item in the text)
                    elif value == len(text) - 1:
                        card_data["company_name"].append(i)
                    
                    # Check for mobile number
                    elif "+" in i or "+91" in i or "-" in i:
                        card_data["mobile_no"].append(i)
                        if len(card_data["mobile_no"])==2:
                            card_data["mobile_no"] = " & " .join(card_data["mobile_no"])
                        
                    # Check for website
                    if "www" in i.lower() or "www." in i.lower():
                        card_data["website"].append(i)
                    elif "WWW" in i:
                        card_data["website"].append(text[4] + "." + text[5])
                        
                    # Check for email ID
                    if "@" in i and ".com" in i:
                        card_data["mail_id"].append(i)
                        
                    # Extract door number
                    if re.findall('^[0-9].+, [a-zA-Z]+', i):
                        card_data["door_no"].append(i.split(',')[0])
                    elif re.findall('[0-9] [a-zA-Z]+', i):
                        card_data["door_no"].append(i)
                        
                    # Extract city
                    match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                    match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                    match3 = re.findall('^[E].*', i)
                    if match1:
                        card_data["city"].append(match1[0])
                    elif match2:
                        card_data["city"].append(match2[0])
                    elif match3:
                        card_data["city"].append(match3[0])

                    # Extract state
                    state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                    if state_match:
                        card_data["state"].append(i[:9])
                    elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                        card_data["state"].append(i.split()[-1])
                    if len(card_data["state"]) == 2:
                        card_data["state"].pop(0)
                
                    # Extract pincode
                    if len(i) >= 6 and i.isdigit():
                        card_data["pincode"].append(i)
                    elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                        card_data["pincode"].append(i[10:]) 
                      
        card_data_ext(result)
        df = pd.DataFrame(card_data)
        st.write(df)
            
        if st.button("Upload data to SQL server"):
            create_mysql_tables()
            connection = mysql_connect()
            mycursor = connection.cursor()
            for index, row in df.iterrows():
                query1 = '''insert into card_data(card_holder_name,
                                                designation,
                                                company_name,
                                                mobile_no,
                                                website,
                                                mail_id,
                                                door_no,
                                                city,
                                                state,
                                                pincode,
                                                image) 
                                                value(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                                                
                                                
                values = (row['card_holder_name'],
                        row['designation'],
                        row['company_name'],
                        row['mobile_no'],
                        row['website'],
                        row['mail_id'],
                        row['door_no'],
                        row['city'],
                        row['state'],
                        row['pincode'],
                        row['image']
                        )
                                                
                mycursor.execute(query1,tuple(row))
                connection.commit()
                st.success("Data Upload to SQL")
elif Select == "View Data":
    st.header("View Data in MySQL")  
    
    def decode(blob):
        img = Image.open(BytesIO(blob))
        return img
    
    connection = mysql_connect()
    mycursor = connection.cursor()
    try: 
        select_query = "SELECT card_holder_name,image FROM card_data"
        mycursor.execute(select_query)
        
        rows = mycursor.fetchall()
            
        card_details  = {}
        for row in rows:
            card_details[row[0]] = row[1]
        options = ['None'] + list(card_details.keys())
        selected_card = st.selectbox("Select a Card", options)
        if selected_card == "None":
            st.write("No Card Selected")
        else: 
            coll1,coll2 = st.columns(2)
            with coll1:
                mycursor.execute('''Select card_holder_name,
                                            designation,
                                            company_name,
                                            mobile_no,
                                            website,
                                            mail_id,
                                            door_no,
                                            city,
                                            state,
                                            pincode,
                                            image from card_data WHERE card_holder_name =%s''',(selected_card,))
                result = mycursor.fetchone()
                
                card_holder_name = st.text_input("Card_holder_name", result[0])
                designation = st.text_input("Designation", result[1])
                company_name = st.text_input("Company_name", result[2])
                mobile_no = st.text_input("Mobile_no", result[3])
                website = st.text_input("Website", result[4])
                mail_id = st.text_input("Mail_id", result[5])
                door_no = st.text_input("Door_no", result[6])
                city = st.text_input("City", result[7])
                state = st.text_input("State", result[8])
                pincode = st.text_input("Pincode", result[9])
            with coll2:
                # Decode and resize image from binary blob
                image_blob = card_details[selected_card]
                image = decode(image_blob)
                st.image(image, caption=f"Card Holder Name: {selected_card}") # Display image with caption
    except:
        st.warning("There is no data in MySQL server")
                  
elif Select == "Make change":
    st.header("Update Data in MySQL")
    try:
        connection = mysql_connect()
        mycursor = connection.cursor()
        
        select_query = "SELECT card_holder_name FROM card_data"
        mycursor.execute(select_query)
        rows = mycursor.fetchall()

        coll1,coll2 = st.columns(2)
        with coll1:               
            card_detial = {}
            for row in rows:
                card_detial[row[0]] = row[0]
            options = ['None'] + list(card_detial.keys())
            selected_card = st.selectbox("Select a Card", options)
            if selected_card == "None":
                st.write("No Card Selected")
            else:
                mycursor.execute('''Select card_holder_name,
                                    designation,
                                    company_name,
                                    mobile_no,
                                    website,
                                    mail_id,
                                    door_no,
                                    city,
                                    state,
                                    pincode from card_data WHERE card_holder_name =%s''',(selected_card,))
                result = mycursor.fetchone()
                
                card_holder_name = st.text_input("Card_holder_name", result[0])
                designation = st.text_input("Designation", result[1])
                company_name = st.text_input("Company_name", result[2])
                mobile_no = st.text_input("Mobile_no", result[3])
                website = st.text_input("Website", result[4])
                mail_id = st.text_input("Mail_id", result[5])
                door_no = st.text_input("Door_no", result[6])
                city = st.text_input("City", result[7])
                state = st.text_input("State", result[8])
                pincode = st.text_input("Pincode", result[9])
                
                if st.button("Update change in MySQL"):
                    mycursor.execute("""UPDATE card_data SET
                                    card_holder_name=%s,
                                    designation=%s,
                                    company_name=%s,
                                    mobile_no=%s,
                                    website=%s,
                                    mail_id=%s,
                                    door_no=%s,
                                    city=%s,
                                    state=%s,
                                    pincode=%s where card_holder_name=%s""",
                                    (card_holder_name,
                                    designation,
                                    company_name,
                                    mobile_no,
                                    website,
                                    mail_id,
                                    door_no,
                                    city,
                                    state,
                                    pincode,selected_card))
                                                        
                    connection.commit()
                    st.success("Correction Data updated in SQL")
    except:
        st.warning("There is no data in MySQL server")

elif Select == "Remove Data":
    st.header("Remove Data in MySQL")

coll1, coll2, coll3, coll4 = st.columns(4)
with coll1:
    try:
        connection = mysql_connect()
        mycursor = connection.cursor()
        select_query = "SELECT card_holder_name FROM card_data"
        mycursor.execute(select_query)
        rows = mycursor.fetchall()
        
        card_detail = {}
        for row in rows:
            card_detail[row[0]] = row[0]
        
        options = ['None'] + list(card_detail.keys())
        selected_card = st.selectbox("Select a Card", options)
        
        if selected_card == "None":
            st.write("No Card Selected")
        else:
            st.write(f"You have selected: {selected_card}. Do you want to delete?")
            if st.button("Confirm Delete"):
                try:
                    mycursor.execute(f"DELETE FROM card_data WHERE card_holder_name = '{selected_card}'")
                    connection.commit()
                    st.success("Selected Card Detail removed from MySQL")
                except mysql.connector.Error as err:
                    st.warning(f"MySQL Error: {err}")
                except Exception as e:
                    st.warning(f"An error occurred: {e}")
    except mysql.connector.Error as err:
        st.warning(f"MySQL Error: {err}")
    except Exception as e:
        st.warning(f"An error occurred: {e}")
