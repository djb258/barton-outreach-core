/**
 * Doctrine Spec:
 * - Barton ID: 13.01.01.07.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Firebase MCP service for real-time data operations
 * - Input: Firebase operations and queries
 * - Output: Firebase data and operation results
 * - MCP: Firebase (Real-time Database & Firestore)
 */

import { initializeApp } from 'firebase/app';
import {
  getFirestore,
  collection,
  doc,
  setDoc,
  getDoc,
  getDocs,
  query,
  where,
  orderBy,
  limit,
  serverTimestamp
} from 'firebase/firestore';
import {
  getDatabase,
  ref,
  set,
  get,
  child,
  push,
  onValue,
  off
} from 'firebase/database';

class FirebaseMCPService {
  constructor() {
    this.app = null;
    this.firestore = null;
    this.rtdb = null;
    this.listeners = new Map();
    this.bartonIdPrefix = '13.01';
  }

  /**
   * Initialize Firebase with MCP configuration
   */
  async initialize() {
    const firebaseConfig = {
      apiKey: process.env.FIREBASE_API_KEY,
      authDomain: process.env.FIREBASE_AUTH_DOMAIN,
      projectId: process.env.FIREBASE_PROJECT_ID,
      storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
      messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
      appId: process.env.FIREBASE_APP_ID,
      databaseURL: process.env.FIREBASE_DATABASE_URL
    };

    try {
      this.app = initializeApp(firebaseConfig);
      this.firestore = getFirestore(this.app);
      this.rtdb = getDatabase(this.app);

      console.log('[FIREBASE-MCP] Service initialized successfully');
      return { success: true };
    } catch (error) {
      console.error('[FIREBASE-MCP] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Firestore Operations
   */

  // Create or update a document with Barton ID
  async createDocument(collectionName, data, docId = null) {
    try {
      const bartonId = this.generateBartonId();
      const documentData = {
        ...data,
        barton_id: bartonId,
        created_at: serverTimestamp(),
        updated_at: serverTimestamp(),
        altitude: 10000
      };

      const docRef = docId
        ? doc(this.firestore, collectionName, docId)
        : doc(collection(this.firestore, collectionName));

      await setDoc(docRef, documentData);

      return {
        success: true,
        id: docRef.id,
        barton_id: bartonId,
        path: `${collectionName}/${docRef.id}`
      };
    } catch (error) {
      console.error('[FIREBASE-MCP] Document creation failed:', error);
      throw error;
    }
  }

  // Get a document by ID
  async getDocument(collectionName, docId) {
    try {
      const docRef = doc(this.firestore, collectionName, docId);
      const docSnap = await getDoc(docRef);

      if (docSnap.exists()) {
        return {
          success: true,
          data: { id: docSnap.id, ...docSnap.data() }
        };
      } else {
        return {
          success: false,
          error: 'Document not found'
        };
      }
    } catch (error) {
      console.error('[FIREBASE-MCP] Document retrieval failed:', error);
      throw error;
    }
  }

  // Query documents with filters
  async queryDocuments(collectionName, filters = {}, options = {}) {
    try {
      let q = collection(this.firestore, collectionName);

      // Build query
      const constraints = [];

      if (filters.where) {
        filters.where.forEach(condition => {
          constraints.push(where(condition.field, condition.operator, condition.value));
        });
      }

      if (options.orderBy) {
        constraints.push(orderBy(options.orderBy.field, options.orderBy.direction || 'asc'));
      }

      if (options.limit) {
        constraints.push(limit(options.limit));
      }

      if (constraints.length > 0) {
        q = query(q, ...constraints);
      }

      const querySnapshot = await getDocs(q);
      const documents = [];

      querySnapshot.forEach((doc) => {
        documents.push({ id: doc.id, ...doc.data() });
      });

      return {
        success: true,
        count: documents.length,
        data: documents
      };
    } catch (error) {
      console.error('[FIREBASE-MCP] Query failed:', error);
      throw error;
    }
  }

  /**
   * Real-time Database Operations
   */

  // Write data to RTDB with Barton ID
  async writeRTDB(path, data) {
    try {
      const bartonId = this.generateBartonId();
      const rtdbData = {
        ...data,
        barton_id: bartonId,
        timestamp: Date.now(),
        altitude: 10000
      };

      const dbRef = ref(this.rtdb, path);
      await set(dbRef, rtdbData);

      return {
        success: true,
        path: path,
        barton_id: bartonId
      };
    } catch (error) {
      console.error('[FIREBASE-MCP] RTDB write failed:', error);
      throw error;
    }
  }

  // Read data from RTDB
  async readRTDB(path) {
    try {
      const dbRef = ref(this.rtdb);
      const snapshot = await get(child(dbRef, path));

      if (snapshot.exists()) {
        return {
          success: true,
          data: snapshot.val()
        };
      } else {
        return {
          success: false,
          error: 'No data available'
        };
      }
    } catch (error) {
      console.error('[FIREBASE-MCP] RTDB read failed:', error);
      throw error;
    }
  }

  // Push data to RTDB list
  async pushRTDB(path, data) {
    try {
      const bartonId = this.generateBartonId();
      const rtdbData = {
        ...data,
        barton_id: bartonId,
        timestamp: Date.now()
      };

      const listRef = ref(this.rtdb, path);
      const newRef = push(listRef);
      await set(newRef, rtdbData);

      return {
        success: true,
        key: newRef.key,
        barton_id: bartonId,
        path: `${path}/${newRef.key}`
      };
    } catch (error) {
      console.error('[FIREBASE-MCP] RTDB push failed:', error);
      throw error;
    }
  }

  // Subscribe to RTDB changes
  subscribeRTDB(path, callback) {
    const dbRef = ref(this.rtdb, path);

    const listener = onValue(dbRef, (snapshot) => {
      callback({
        path: path,
        data: snapshot.val(),
        timestamp: new Date().toISOString()
      });
    }, (error) => {
      console.error('[FIREBASE-MCP] Subscription error:', error);
      callback({
        error: error.message,
        path: path
      });
    });

    // Store listener reference
    const listenerId = `${path}_${Date.now()}`;
    this.listeners.set(listenerId, { ref: dbRef, listener });

    return listenerId;
  }

  // Unsubscribe from RTDB changes
  unsubscribeRTDB(listenerId) {
    const listenerData = this.listeners.get(listenerId);
    if (listenerData) {
      off(listenerData.ref, 'value', listenerData.listener);
      this.listeners.delete(listenerId);
      return { success: true };
    }
    return { success: false, error: 'Listener not found' };
  }

  /**
   * Lead Scoring Operations (Step 8 Integration)
   */

  // Store lead score in Firebase
  async updateLeadScore(leadId, scoreData) {
    const leadScoreData = {
      lead_id: leadId,
      score: scoreData.score,
      factors: scoreData.factors,
      triggers: scoreData.triggers,
      calculated_at: serverTimestamp(),
      barton_id: this.generateBartonId()
    };

    // Store in Firestore for querying
    await this.createDocument('lead_scores', leadScoreData, leadId);

    // Store in RTDB for real-time updates
    await this.writeRTDB(`lead_scores/${leadId}`, leadScoreData);

    return {
      success: true,
      leadId,
      score: scoreData.score
    };
  }

  // Get top scoring leads
  async getTopLeads(limit = 10) {
    return await this.queryDocuments('lead_scores', [], {
      orderBy: { field: 'score', direction: 'desc' },
      limit: limit
    });
  }

  // Subscribe to lead score changes
  subscribeToLeadScores(callback) {
    return this.subscribeRTDB('lead_scores', (data) => {
      if (!data.error) {
        // Process lead scores and trigger actions
        const leads = Object.entries(data.data || {}).map(([id, lead]) => ({
          id,
          ...lead
        }));

        // Filter high-score leads for immediate action
        const hotLeads = leads.filter(lead => lead.score >= 80);

        callback({
          totalLeads: leads.length,
          hotLeads: hotLeads,
          timestamp: data.timestamp
        });
      }
    });
  }

  /**
   * Campaign Tracking
   */

  async trackCampaignEvent(campaignId, eventType, eventData) {
    const event = {
      campaign_id: campaignId,
      event_type: eventType,
      event_data: eventData,
      timestamp: serverTimestamp(),
      barton_id: this.generateBartonId()
    };

    // Store in both Firestore and RTDB
    await this.createDocument(`campaigns/${campaignId}/events`, event);
    await this.pushRTDB(`campaign_events/${campaignId}`, event);

    return {
      success: true,
      campaignId,
      eventType
    };
  }

  /**
   * Generate Barton ID with Firebase prefix
   */
  generateBartonId() {
    const segment3 = Math.floor(Math.random() * 100).toString().padStart(2, '0');
    const segment4 = '07'; // Firebase operations
    const segment5 = Math.floor(Math.random() * 100000).toString().padStart(5, '0');
    const segment6 = Math.floor(Math.random() * 1000).toString().padStart(3, '0');

    return `${this.bartonIdPrefix}.${segment3}.${segment4}.${segment5}.${segment6}`;
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      // Test Firestore
      const testDoc = await this.getDocument('_health', 'check');

      // Test RTDB
      const testRTDB = await this.readRTDB('_health/check');

      return {
        firestore: testDoc.success || true,
        rtdb: testRTDB.success || true,
        listeners: this.listeners.size,
        healthy: true
      };
    } catch (error) {
      return {
        healthy: false,
        error: error.message
      };
    }
  }
}

export default FirebaseMCPService;