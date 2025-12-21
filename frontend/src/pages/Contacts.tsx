import { useState, useEffect } from 'react';
import { Plus, Search, Phone, Edit2, Trash2, User, Mail, Building, Tag } from 'lucide-react';
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
      // TODO: Replace with API call when backend endpoint is ready
      // For now, use localStorage
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
    // Navigate to test bot with pre-filled number
    window.location.href = `/dashboard/test?phone=${encodeURIComponent(phone)}`;
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
            <h1 className="text-3xl font-bold text-gray-900">Contacts</h1>
            <p className="text-gray-600 mt-1">Manage your contact list for quick dialing</p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Add Contact</span>
          </button>
        </div>

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
                <button
                  onClick={() => setShowAddModal(true)}
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Contact</span>
                </button>
              )}
            </div>
          ) : (
            filteredContacts.map((contact) => (
              <div key={contact.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
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

                  <button
                    onClick={() => handleQuickCall(contact.phone)}
                    className="w-full mt-4 flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <Phone className="w-4 h-4" />
                    <span>Call Now</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

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
