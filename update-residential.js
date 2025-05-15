const fs = require('fs');
const admin = require('firebase-admin');
// const serviceAccount = require('./serviceAccountKey.json');
const serviceAccount = require('./rera-serviceAccountKey.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

function loadDataset(filePath) {
  const rawData = fs.readFileSync(filePath);
  return JSON.parse(rawData);
}

async function updateFirestoreDocuments(dataset) {
  for (const record of dataset) {
    const docRef = db.collection('test-residential').doc(record.id);

    try {
      await docRef.set(record, { merge: true });
      console.log(`Document with ID ${record.id} has been successfully updated.`);
    } catch (error) {
      console.error(`Error updating document with ID ${record.id}:`, error);
    }
  }
  console.log("done")
}

async function main() {
  const inputFilePath = './residential/final-rera-residential.json';
  const dataset = loadDataset(inputFilePath);
  await updateFirestoreDocuments(dataset);
}

main().catch(console.error);
