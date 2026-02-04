"""Verify column mapping for appointments file."""
import pandas as pd

df = pd.read_csv(r'C:\Users\CUSTOM PC\Desktop\appts-already-had-2129971 full email addresses.csv')

print('=== COLUMN LETTER MAPPING ===')
cols = list(df.columns)
for i, col in enumerate(cols[:20]):
    letter = chr(65 + i)  # A, B, C, etc.
    print(f'{letter} (col {i+1}): {col}')

print('\n=== SAMPLE OF ORIGINAL APPOINTMENT CONTACTS ===')
# E=First, F=Last, G=Title, H=Company, O=Area, P=Phone, Q=Email
sample = df[['First', 'Last', 'Title', 'Company', 'Area', 'Phone', 'Email']].drop_duplicates(subset=['Company']).head(15)
print(sample.to_string())

print('\n=== STATS ===')
unique_appts = df.drop_duplicates(subset=['Company'])
print(f'Unique appointment contacts: {len(unique_appts)}')
print(f'With email: {unique_appts["Email"].notna().sum()}')
print(f'With phone: {unique_appts["Phone"].notna().sum()}')

print('\n=== SAMPLE TITLES ===')
print(unique_appts['Title'].value_counts().head(20))
