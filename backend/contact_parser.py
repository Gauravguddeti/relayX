"""
Smart CSV/Excel/TXT parser for bulk campaign contacts.
Handles variable column structures - only requires phone number, everything else is flexible.
"""
import pandas as pd
import phonenumbers
from phonenumbers import NumberParseException
from typing import List, Dict, Optional
import re
from io import BytesIO

class ContactParser:
    """Flexible contact parser that handles various file formats and column structures"""
    
    # Common phone number column names (case-insensitive)
    PHONE_PATTERNS = [
        'phone', 'phone_number', 'phonenumber', 'mobile', 'cell', 'telephone', 
        'tel', 'contact', 'number', 'phone #', 'cell phone'
    ]
    
    # Common name column names
    NAME_PATTERNS = [
        'name', 'full_name', 'fullname', 'contact_name', 'customer_name',
        'first_name', 'firstname', 'last_name', 'lastname', 'client'
    ]
    
    def __init__(self, default_country='US'):
        """
        Initialize parser with default country code for phone normalization
        
        Args:
            default_country: ISO country code (US, IN, GB, etc.)
        """
        self.default_country = default_country
    
    def parse_file(self, file_content: bytes, filename: str) -> tuple[List[Dict], List[str]]:
        """
        Parse uploaded file and extract contacts
        
        Returns:
            tuple: (parsed_contacts list, errors list)
        """
        try:
            # Detect file type and parse
            if filename.endswith('.csv'):
                df = pd.read_csv(BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(BytesIO(file_content))
            elif filename.endswith('.txt'):
                # Try to parse as CSV with various delimiters
                content = file_content.decode('utf-8')
                df = self._parse_txt(content)
            else:
                return [], [f"Unsupported file type: {filename}"]
            
            # Extract contacts
            return self._extract_contacts(df)
            
        except Exception as e:
            return [], [f"Error parsing file: {str(e)}"]
    
    def _parse_txt(self, content: str) -> pd.DataFrame:
        """Parse TXT file - try common delimiters"""
        # Try comma, tab, pipe, semicolon
        for delimiter in [',', '\t', '|', ';']:
            try:
                df = pd.read_csv(BytesIO(content.encode()), delimiter=delimiter)
                if len(df.columns) > 1:
                    return df
            except:
                continue
        
        # Fallback: parse line by line (Name - Phone format)
        lines = content.strip().split('\n')
        data = []
        for line in lines:
            parts = re.split(r'[-–—]', line, 1)
            if len(parts) == 2:
                data.append({'name': parts[0].strip(), 'phone': parts[1].strip()})
            elif re.search(r'\d{10,}', line):
                data.append({'phone': line.strip()})
        
        return pd.DataFrame(data) if data else pd.DataFrame()
    
    def _extract_contacts(self, df: pd.DataFrame) -> tuple[List[Dict], List[str]]:
        """Extract and normalize contacts from DataFrame"""
        contacts = []
        errors = []
        
        if df.empty:
            return [], ["File is empty or could not be parsed"]
        
        # Find phone and name columns (case-insensitive)
        phone_col = self._find_column(df, self.PHONE_PATTERNS)
        name_col = self._find_column(df, self.NAME_PATTERNS)
        
        if not phone_col:
            return [], ["Could not find phone number column. Expected columns like: phone, mobile, number, etc."]
        
        # Get all other columns for metadata
        metadata_cols = [col for col in df.columns if col not in [phone_col, name_col]]
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Extract phone
                phone_raw = str(row[phone_col]).strip()
                if pd.isna(phone_raw) or phone_raw == '' or phone_raw.lower() == 'nan':
                    errors.append(f"Row {idx + 2}: Missing phone number")
                    continue
                
                # Normalize phone number
                phone_normalized = self._normalize_phone(phone_raw)
                if not phone_normalized:
                    errors.append(f"Row {idx + 2}: Invalid phone number '{phone_raw}'")
                    continue
                
                # Extract name (optional)
                name = None
                if name_col:
                    name_raw = row[name_col]
                    if not pd.isna(name_raw):
                        name = str(name_raw).strip()
                
                # Extract metadata from other columns
                metadata = {}
                for col in metadata_cols:
                    val = row[col]
                    if not pd.isna(val):
                        # Convert to appropriate type
                        if isinstance(val, (int, float)):
                            metadata[col] = val
                        else:
                            metadata[col] = str(val).strip()
                
                # Build contact
                contact = {
                    'phone': phone_normalized,
                    'name': name,
                    'metadata': metadata
                }
                contacts.append(contact)
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        # Deduplicate by phone number
        seen_phones = set()
        unique_contacts = []
        duplicates = 0
        
        for contact in contacts:
            if contact['phone'] not in seen_phones:
                seen_phones.add(contact['phone'])
                unique_contacts.append(contact)
            else:
                duplicates += 1
        
        if duplicates > 0:
            errors.append(f"Removed {duplicates} duplicate phone number(s)")
        
        return unique_contacts, errors
    
    def _find_column(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        """Find column matching any of the patterns (case-insensitive)"""
        cols_lower = {col.lower(): col for col in df.columns}
        
        for pattern in patterns:
            if pattern in cols_lower:
                return cols_lower[pattern]
            
            # Partial match
            for col_lower, col_original in cols_lower.items():
                if pattern in col_lower:
                    return col_original
        
        return None
    
    def _normalize_phone(self, phone_raw: str) -> Optional[str]:
        """
        Normalize phone number to E.164 format (+12025551234)
        
        Handles various formats:
        - (202) 555-1234
        - 202-555-1234
        - 2025551234
        - +1 202 555 1234
        """
        try:
            # Remove common non-digit characters
            cleaned = re.sub(r'[^\d+]', '', phone_raw)
            
            # Parse with phonenumbers library
            parsed = phonenumbers.parse(cleaned, self.default_country)
            
            # Validate
            if not phonenumbers.is_valid_number(parsed):
                return None
            
            # Return E.164 format
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            
        except NumberParseException:
            return None
        except Exception:
            return None
