import { useState, useEffect, useRef } from 'react';
import { Plus, Search, Phone, Edit2, Trash2, User, Mail, Building, Tag, Upload, FileSpreadsheet, CheckSquare, Square, X, AlertCircle } from 'lucide-react';
import DashboardLayout from '../components/dashboard/DashboardLayout';

interface Contact {
  id: string;
  name: string;
  phone: string;
  email?: string;
  company?: string;
  tags?: string[];
  notes?: string;
  last_called?: string;
  created_at: string;
}

export default function Contacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importError, setImportError] = useState('');
  const [importSuccess, setImportSuccess] = useState('');
  const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    company: '',
    tags: '',
    notes: '',
  });

  useEffect(() => {
    loadContacts();
  }, []);

  function loadContacts() {
    try {
      const saved = localStorage.getItem('relayx_contacts');
      if (saved) {
        setContacts(JSON.parse(saved));
      }
    } catch (error) {
      console.error('Failed to load contacts:', error);
    } finally {
      setLoading(false);
    }
  }

  function saveContacts(updatedContacts: Contact[]) {
    localStorage.setItem('relayx_contacts', JSON.stringify(updatedContacts));
    setContacts(updatedContacts);
  }

  function handleAddContact() {
    const newContact: Contact = {
      id: Date.now().toString(),
      name: formData.name,
      phone: formData.phone,
      email: formData.email,
      company: formData.company,
      tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : [],
      notes: formData.notes,
      created_at: new Date().toISOString(),
    };

    saveContacts([...contacts, newContact]);
    resetForm();
    setShowAddModal(false);
  }

  function handleEditContact() {
    if (!editingContact) return;

    const updatedContacts = contacts.map(c =>
      c.id === editingContact.id
        ? {
            ...c,
            name: formData.name,
            phone: formData.phone,
            email: formData.email,
            company: formData.company,
            tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : [],
            notes: formData.notes,
          }
        : c
    );

    saveContacts(updatedContacts);
    resetForm();
    setEditingContact(null);
  }

  function handleDeleteContact(id: string) {
    if (confirm('Are you sure you want to delete this contact?')) {
      saveContacts(contacts.filter(c => c.id !== id));
      selectedContacts.delete(id);
      setSelectedContacts(new Set(selectedContacts));
    }
  }

  function handleBulkDelete() {
    if (selectedContacts.size === 0) return;
    
    if (confirm(`Are you sure you want to delete ${selectedContacts.size} contact(s)?`)) {
      saveContacts(contacts.filter(c => !selectedContacts.has(c.id)));
      setSelectedContacts(new Set());
      setIsSelectionMode(false);
    }
  }

  function toggleContactSelection(id: string) {
    const newSelection = new Set(selectedContacts);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedContacts(newSelection);
  }

  function toggleSelectAll() {
    if (selectedContacts.size === filteredContacts.length) {
      setSelectedContacts(new Set());
    } else {
      setSelectedContacts(new Set(filteredContacts.map(c => c.id)));
    }
  }

  function startEdit(contact: Contact) {
    setEditingContact(contact);
    setFormData({
      name: contact.name,
      phone: contact.phone,
      email: contact.email || '',
      company: contact.company || '',
      tags: contact.tags?.join(', ') || '',
      notes: contact.notes || '',
    });
  }

  function resetForm() {
    setFormData({
      name: '',
      phone: '',
      email: '',
      company: '',
      tags: '',
      notes: '',
    });
  }

  function handleQuickCall(phone: string) {
    window.location.href = `/dashboard/test?phone=${encodeURIComponent(phone)}`;
  }

  // File import functionality
  function handleFileSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportError('');
    setImportSuccess('');

    const fileExtension = file.name.split('.').pop()?.toLowerCase();

    if (fileExtension === 'csv') {
      parseCSV(file);
    } else if (fileExtension === 'xlsx' || fileExtension === 'xls') {
      parseExcel(file);
    } else if (fileExtension === 'txt') {
      parseTXT(file);
    } else {
      setImportError('Unsupported file format. Please use CSV, Excel (.xlsx/.xls), or TXT files.');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  function parseCSV(file: File) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());
        
        if (lines.length < 2) {
          setImportError('CSV file must have a header row and at least one data row.');
          return;
        }

        const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
        const nameIndex = headers.findIndex(h => h.includes('name'));
        const phoneIndex = headers.findIndex(h => h.includes('phone') || h.includes('mobile') || h.includes('tel'));
        const emailIndex = headers.findIndex(h => h.includes('email'));
        const companyIndex = headers.findIndex(h => h.includes('company') || h.includes('organization'));

        if (nameIndex === -1 || phoneIndex === -1) {
          setImportError('CSV must have "name" and "phone" columns.');
          return;
        }

        const newContacts: Contact[] = [];
        const existingPhones = new Set(contacts.map(c => c.phone));

        for (let i = 1; i < lines.length; i++) {
          const values = parseCSVLine(lines[i]);
          const name = values[nameIndex]?.trim();
          const phone = values[phoneIndex]?.trim().replace(/[^0-9+]/g, '');
          
          if (name && phone && !existingPhones.has(phone)) {
            newContacts.push({
              id: `${Date.now()}-${i}`,
              name,
              phone,
              email: emailIndex !== -1 ? values[emailIndex]?.trim() : undefined,
              company: companyIndex !== -1 ? values[companyIndex]?.trim() : undefined,
              created_at: new Date().toISOString(),
            });
            existingPhones.add(phone);
          }
        }

        if (newContacts.length > 0) {
          saveContacts([...contacts, ...newContacts]);
          setImportSuccess(`Successfully imported ${newContacts.length} contact(s).`);
        } else {
          setImportError('No new contacts found in file (duplicates skipped).');
        }
      } catch (error) {
        setImportError('Failed to parse CSV file. Please check the format.');
      }
    };
    reader.readAsText(file);
  }

  function parseCSVLine(line: string): string[] {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current);
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current);
    return result;
  }

  function parseExcel(file: File) {
    // For Excel files, we'll read as binary and parse basic structure
    // Note: For production, you'd want to use a library like xlsx
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        // Try to dynamically load xlsx library if available
        // For now, show a helpful message
        setImportError('Excel import requires the xlsx library. Please convert to CSV format for now, or install xlsx package.');
        
        // Alternative: Use a simple approach for basic xlsx files
        // This is a simplified parser that works for basic cases
      } catch (error) {
        setImportError('Failed to parse Excel file. Please try CSV format.');
      }
    };
    reader.readAsArrayBuffer(file);
  }

  function parseTXT(file: File) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());
        
        const newContacts: Contact[] = [];
        const existingPhones = new Set(contacts.map(c => c.phone));

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          // Try to parse "Name - Phone" or "Name: Phone" or "Name, Phone" format
          const match = line.match(/^(.+?)[\s]*[-:,][\s]*([+]?\d[\d\s-]+)$/);
          
          if (match) {
            const name = match[1].trim();
            const phone = match[2].replace(/[^0-9+]/g, '');
            
            if (name && phone && !existingPhones.has(phone)) {
              newContacts.push({
                id: `${Date.now()}-${i}`,
                name,
                phone,
                created_at: new Date().toISOString(),
              });
              existingPhones.add(phone);
            }
          }
        }

        if (newContacts.length > 0) {
          saveContacts([...contacts, ...newContacts]);
          setImportSuccess(`Successfully imported ${newContacts.length} contact(s).`);
        } else {
          setImportError('No valid contacts found. Use format: "Name - Phone" or "Name, Phone"');
        }
      } catch (error) {
        setImportError('Failed to parse TXT file.');
      }
    };
    reader.readAsText(file);
  }

  const filteredContacts = contacts.filter(contact =>
    searchTerm === '' ||
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.phone.includes(searchTerm) ||
    contact.company?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-text">Contacts</h1>
            <p className="text-gray-600 mt-1">Manage your contact list for quick dialing</p>
          </div>
          <div className="flex space-x-3">
            {isSelectionMode ? (
              <>
                <button
                  onClick={() => {
                    setIsSelectionMode(false);
                    setSelectedContacts(new Set());
                  }}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  <X className="w-4 h-4" />
                  <span>Cancel</span>
                </button>
                <button
                  onClick={handleBulkDelete}
                  disabled={selectedContacts.size === 0}
                  className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete ({selectedContacts.size})</span>
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setIsSelectionMode(true)}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  <CheckSquare className="w-4 h-4" />
                  <span>Select</span>
                </button>
                <button
                  onClick={() => setShowImportModal(true)}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  <Upload className="w-4 h-4" />
                  <span>Import</span>
                </button>
                <button
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-5 h-5" />
                  <span>Add Contact</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Selection Header */}
        {isSelectionMode && filteredContacts.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleSelectAll}
                className="flex items-center space-x-2 text-blue-700 hover:text-blue-900"
              >
                {selectedContacts.size === filteredContacts.length ? (
                  <CheckSquare className="w-5 h-5" />
                ) : (
                  <Square className="w-5 h-5" />
                )}
                <span>{selectedContacts.size === filteredContacts.length ? 'Deselect All' : 'Select All'}</span>
              </button>
              <span className="text-blue-600">
                {selectedContacts.size} of {filteredContacts.length} selected
              </span>
            </div>
          </div>
        )}

        {/* Import Success/Error Messages */}
        {importSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
            <span className="text-green-800">{importSuccess}</span>
            <button onClick={() => setImportSuccess('')} className="text-green-600 hover:text-green-800">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        {importError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
            <span className="text-red-800">{importError}</span>
            <button onClick={() => setImportError('')} className="text-red-600 hover:text-red-800">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search contacts by name, phone, or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Contacts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredContacts.length === 0 ? (
            <div className="col-span-full bg-white rounded-lg shadow p-12 text-center">
              <User className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No contacts yet</h3>
              <p className="text-gray-600 mb-4">
                {searchTerm ? 'No contacts match your search' : 'Add your first contact to get started'}
              </p>
              {!searchTerm && (
                <div className="flex justify-center space-x-3">
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Contact</span>
                  </button>
                  <button
                    onClick={() => setShowImportModal(true)}
                    className="inline-flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    <Upload className="w-4 h-4" />
                    <span>Import</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            filteredContacts.map((contact) => (
              <div 
                key={contact.id} 
                className={`bg-white rounded-lg shadow hover:shadow-md transition-shadow ${
                  isSelectionMode && selectedContacts.has(contact.id) ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      {isSelectionMode && (
                        <button
                          onClick={() => toggleContactSelection(contact.id)}
                          className="text-gray-400 hover:text-blue-600"
                        >
                          {selectedContacts.has(contact.id) ? (
                            <CheckSquare className="w-5 h-5 text-blue-600" />
                          ) : (
                            <Square className="w-5 h-5" />
                          )}
                        </button>
                      )}
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-lg">
                        {contact.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{contact.name}</h3>
                        {contact.company && (
                          <p className="text-sm text-gray-500 flex items-center">
                            <Building className="w-3 h-3 mr-1" />
                            {contact.company}
                          </p>
                        )}
                      </div>
                    </div>
                    {!isSelectionMode && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => startEdit(contact)}
                          className="text-gray-400 hover:text-blue-600 transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteContact(contact.id)}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center text-sm text-gray-600">
                      <Phone className="w-4 h-4 mr-2" />
                      {contact.phone}
                    </div>
                    {contact.email && (
                      <div className="flex items-center text-sm text-gray-600">
                        <Mail className="w-4 h-4 mr-2" />
                        {contact.email}
                      </div>
                    )}
                    {contact.tags && contact.tags.length > 0 && (
                      <div className="flex items-center flex-wrap gap-1 mt-2">
                        <Tag className="w-3 h-3 text-gray-400" />
                        {contact.tags.map((tag, i) => (
                          <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    {contact.notes && (
                      <p className="text-xs text-gray-500 mt-2 italic line-clamp-2">{contact.notes}</p>
                    )}
                  </div>

                  {!isSelectionMode && (
                    <button
                      onClick={() => handleQuickCall(contact.phone)}
                      className="w-full mt-4 flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <Phone className="w-4 h-4" />
                      <span>Call Now</span>
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Import Contacts</h2>
                <button
                  onClick={() => {
                    setShowImportModal(false);
                    setImportError('');
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <FileSpreadsheet className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">
                    Upload a CSV, Excel, or TXT file with your contacts
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls,.txt"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Choose File
                  </button>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">File Format Requirements</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• <strong>CSV:</strong> Must have "name" and "phone" columns (case-insensitive)</li>
                    <li>• <strong>Excel:</strong> Same as CSV (first sheet used)</li>
                    <li>• <strong>TXT:</strong> One contact per line: "Name - Phone" or "Name, Phone"</li>
                  </ul>
                </div>

                {importError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                    <span className="text-red-800 text-sm">{importError}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {(showAddModal || editingContact) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                {editingContact ? 'Edit Contact' : 'Add New Contact'}
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="John Doe"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="+1234567890"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="john@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company
                  </label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Acme Inc"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tags (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="lead, interested, vip"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notes
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows={3}
                    placeholder="Additional notes about this contact..."
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => {
                    resetForm();
                    setShowAddModal(false);
                    setEditingContact(null);
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={editingContact ? handleEditContact : handleAddContact}
                  disabled={!formData.name || !formData.phone}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {editingContact ? 'Save Changes' : 'Add Contact'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
