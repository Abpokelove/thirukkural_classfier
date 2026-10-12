# Cloud Computing Lab Cheat Sheet

This is a self-contained beginner manual for the experiments in the lab PDFs, with missing or cut-off steps reconstructed as working examples. Experiments 1 and 7 are intentionally omitted as requested.

Important:
- Each project is independent. Create its own folder; do not combine different `package.json` files.
- Commands are marked for Ubuntu/Linux, Windows PowerShell, or the application's own console. Do not paste shell commands into a JavaScript/Scala/C console.
- Substitute every `YOUR_...` placeholder. Never publish API keys, tokens, passwords, or `.env` files.
- Cloud accounts/services require internet access and may require account verification or billing. No offline sheet can replace those external requirements. For offline practice, use the local alternatives noted in each experiment.
- Use the official links as reference/installation links. The procedure and working example are included here so a reference website is not needed during the lab.
- On Windows, use `curl.exe` only if installed; otherwise use `Invoke-WebRequest -Uri URL -OutFile FILE`.

---

## Quick Setup and Project Conventions

### Ubuntu/Linux common setup
```bash
sudo apt update
sudo apt install -y curl wget git unzip build-essential
node -v
npm -v
java -version
```

### Windows PowerShell checks
```powershell
node --version
npm --version
java -version
python --version
```

### If Java is missing
```bash
sudo apt install -y openjdk-17-jdk
java -version
```

### If Node.js is missing
Install the current Node.js LTS from [nodejs.org](https://nodejs.org/en/download). Close and reopen the terminal, then run `node --version` and `npm --version`.

### If an npm project has no run command
```bash
npm pkg set scripts.start="node server.js"
npm start
```

### Important note about lab code
The RAM-only REST example in Experiment 2C is intentionally a small API exercise: its records reset when the server restarts. Use the MongoDB experiment for persistent CRUD. Keep all pages and files for one application in the same project folder.

---

## 3) Experiment 2A: Building RESTful API with Express.js

### Aim
Explore RESTful API design with Express.js.

### Useful links
- [Node.js installation](https://nodejs.org/en/download)
- [Express.js official guide](https://expressjs.com/en/starter/installing.html)
- [IBM SkillsBuild](https://skillsbuild.org/) (sign-in/course completion may be required by the lab)

This is an API-only experiment; Postman or `curl` is the client, so a browser UI/CSS is not required.

### Commands
```bash
mkdir api-demo
cd api-demo
npm init -y
npm install express
```

Create `app.js` in this folder, paste the code below, then run `node app.js`.

### Working Express REST API template
```js
const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

let users = [
  { id: 1, name: 'Alice', email: 'alice@example.com' },
  { id: 2, name: 'Bob', email: 'bob@example.com' }
];

app.get('/', (req, res) => {
  res.send('REST API is running');
});

app.get('/api/users', (req, res) => {
  res.json(users);
});

app.get('/api/users/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const user = users.find(u => u.id === id);
  if (!user) return res.status(404).json({ message: 'User not found' });
  res.json(user);
});

app.post('/api/users', (req, res) => {
  const { name, email } = req.body;
  if (!name || !email) return res.status(400).json({ message: 'Name and email required' });

  const newUser = { id: users.length ? users[users.length - 1].id + 1 : 1, name, email };
  users.push(newUser);
  res.status(201).json(newUser);
});

app.put('/api/users/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const index = users.findIndex(u => u.id === id);
  if (index === -1) return res.status(404).json({ message: 'User not found' });

  users[index] = { ...users[index], ...req.body };
  res.json(users[index]);
});

app.delete('/api/users/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const index = users.findIndex(u => u.id === id);
  if (index === -1) return res.status(404).json({ message: 'User not found' });

  const deleted = users.splice(index, 1)[0];
  res.json({ message: 'User deleted', user: deleted });
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
```

### Run it
```bash
node app.js
```

### Browser/HTTP tests
```bash
curl http://localhost:3000/api/users
```

### Check all API operations
Use Postman, select **Body -> raw -> JSON** for POST/PUT, and set `Content-Type: application/json`.

| Operation | Method and URL | Example JSON body |
|---|---|---|
| List | `GET http://localhost:3000/api/users` | none |
| Read one | `GET http://localhost:3000/api/users/1` | none |
| Create | `POST http://localhost:3000/api/users` | `{"name":"Sam","email":"sam@example.com"}` |
| Replace/update fields | `PUT http://localhost:3000/api/users/1` | `{"name":"Asha","email":"asha@example.com"}` |
| Delete | `DELETE http://localhost:3000/api/users/1` | none |

`curl` backup (Linux/macOS/Git Bash):
```bash
curl -X POST http://localhost:3000/api/users -H "Content-Type: application/json" -d '{"name":"Sam","email":"sam@example.com"}'
curl -X PUT http://localhost:3000/api/users/1 -H "Content-Type: application/json" -d '{"name":"Asha","email":"asha@example.com"}'
curl -X DELETE http://localhost:3000/api/users/1
```

### If it fails
- `Cannot find module 'express'`: from the project folder run `npm install express`.
- `Cannot find module ... app.js`: confirm the current directory and filename (`Get-ChildItem` on PowerShell, `ls` on Linux).
- `EADDRINUSE`: change `PORT` to another free number, e.g. `3001`, and use that port in Postman.
- `req.body` is undefined: keep `app.use(express.json())` before the routes and send valid JSON with `Content-Type: application/json`.
- Data disappears on restart: expected; this sample stores data in memory only.

---

## 4) Experiment 2B: Consuming Third-Party APIs with Express

### Aim
Integrate a third-party API into an Express app.

### Useful links
- [NASA APOD API page and key](https://api.nasa.gov/)
- [NASA APOD endpoint documentation](https://github.com/nasa/apod-api)
- [Express.js](https://expressjs.com/en/starter/installing.html)

### Example: NASA APOD API

#### Install dependencies
```bash
mkdir nasa-apod
cd nasa-apod
npm init -y
npm install express dotenv
```

#### `.env`
```env
PORT=5000
NASA_API_KEY=YOUR_API_KEY_HERE
```

Create `server.js` and `public/index.html` using the examples below. The server itself serves the page, so open `http://localhost:5000`; do not double-click the HTML file.

#### `server.js`
```js
require('dotenv').config({ quiet: true });
const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 5000;
const API_URL = 'https://api.nasa.gov/planetary/apod';
const API_KEY = process.env.NASA_API_KEY;

if (!API_KEY) {
  console.error('NASA API key is missing in .env file');
  process.exit(1);
}

app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/apod', async (req, res) => {
  try {
    const selectedDate = req.query.date || '2024-01-01';
    const url = new URL(API_URL);
    url.searchParams.append('api_key', API_KEY);
    url.searchParams.append('date', selectedDate);
    url.searchParams.append('thumbs', 'true');

    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({ error: data.error?.message || data.msg || 'NASA request failed' });
    }

    res.json(data);
  } catch (error) {
    console.error('NASA API error:', error.message);
    res.status(500).json({ error: 'Unable to retrieve NASA data' });
  }
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
```

#### Simple frontend `public/index.html`
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>NASA APOD Explorer</title>
  <style>
    * { box-sizing: border-box; }
    body { max-width: 850px; margin: 32px auto; padding: 0 18px; color: #222; background: #fff; font: 16px/1.5 Arial, sans-serif; }
    main { border: 1px solid #ddd; border-radius: 8px; padding: 22px; }
    input, button { padding: 9px 12px; font: inherit; }
    button { color: #fff; background: #333; border: 0; border-radius: 4px; cursor: pointer; }
    img { display: block; max-width: 100%; height: auto; margin: 14px 0; }
    #message { min-height: 1.5em; }
  </style>
</head>
<body>
  <main>
    <h1>NASA Astronomy Picture of the Day</h1>
    <label for="dateInput">Choose a date:</label>
    <input type="date" id="dateInput" value="2024-01-01" />
    <button type="button" onclick="getNasaData()">Load</button>
    <p id="message" role="status"></p>
    <section id="result" hidden>
      <h2 id="title"></h2>
      <p id="date"></p>
      <p id="mediaType"></p>
      <img id="apodImage" alt="NASA astronomy picture" hidden />
      <a id="mediaLink" href="#">Open media</a>
      <p id="explanation"></p>
    </section>
  </main>

  <script>
    const d = document.getElementById('dateInput');
    const m = document.getElementById('message');
    const r = document.getElementById('result');
    const t = document.getElementById('title');
    const dt = document.getElementById('date');
    const mt = document.getElementById('mediaType');
    const i = document.getElementById('apodImage');
    const l = document.getElementById('mediaLink');
    const e = document.getElementById('explanation');

    async function getNasaData() {
      m.innerText = 'Loading...';
      r.hidden = true;
      try {
        const res = await fetch(`/api/apod?date=${d.value}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Fetch failed');

        t.innerText = data.title;
        dt.innerText = data.date;
        mt.innerText = data.media_type;
        e.innerText = data.explanation;

        if (data.media_type === 'image') {
          i.src = data.url;
          i.hidden = false;
          l.href = data.hdurl || data.url;
          l.innerText = 'Open Image';
        } else {
          i.hidden = true;
          l.href = data.url;
          l.innerText = 'Open Video';
        }

        m.innerText = 'NASA data loaded successfully.';
        r.hidden = false;
      } catch (err) {
        m.innerText = err.message;
      }
    }
  </script>
</body>
</html>
```

#### Run and verify
```bash
node server.js
```
Open `http://localhost:5000`, choose a date, and click **Load**. API-only backup: browse to `http://localhost:5000/api/apod?date=2024-01-01`.

### Backup if fetch fails
Node.js 18 or newer includes `fetch`. Check `node --version`; if using an older version, upgrade to current LTS rather than adding an incompatible `node-fetch` import to this CommonJS example. If NASA is unreachable or rate-limited, retry later or use the provided sample JSON response locally; a live third-party result cannot be guaranteed offline.

### If it fails
- `NASA API key is missing`: put `NASA_API_KEY=...` in `.env` beside `server.js`, then restart the server. Do not put the key in browser JavaScript.
- `Cannot GET /`: create `public/index.html` in a folder named exactly `public`.
- `Invalid date`: use a valid date in `YYYY-MM-DD` format and not a future date.
- `429`/rate limit: wait and retry; use NASA's demo key for a brief test if no key is available.
- Browser shows a network error: check the Node terminal for the error and verify internet access. The local page/API works only while `node server.js` is running.

---

## 5) Experiment 2C: RESTful API with CRUD and Postman Testing

### Aim
Build a CRUD API using Express.js, validate request data, and test with Postman.

### Useful links
- [Node.js LTS download](https://nodejs.org/en/download)
- [Express.js guide](https://expressjs.com/en/starter/installing.html)
- [Joi API reference](https://joi.dev/api/)
- [Postman download](https://www.postman.com/downloads/)

### Working compatible code
Create a clean project and save the code as `app.js`:
```bash
mkdir movie-api
cd movie-api
npm init -y
npm install express joi
```

```js
const express = require('express');
const Joi = require('joi');
const app = express();
const PORT = 8080;

app.use(express.json());

const movieSchema = Joi.object({
  title: Joi.string().required(),
  genre: Joi.string().required(),
  director: Joi.string().required(),
  releaseYear: Joi.number().integer().min(1900).max(2100).required(),
  rating: Joi.number().min(0).max(10).required(),
  status: Joi.string().required()
});

let movies = [
  {
    id: 1,
    title: 'Interstellar',
    genre: 'Science Fiction',
    director: 'Christopher Nolan',
    releaseYear: 2014,
    rating: 9,
    status: 'Watched'
  },
  {
    id: 2,
    title: 'The Martian',
    genre: 'Science Fiction',
    director: 'Ridley Scott',
    releaseYear: 2015,
    rating: 8.5,
    status: 'Favourite'
  }
];

app.get('/', (req, res) => {
  res.send('Welcome to the CineTrack Movie Management API');
});

app.get('/api/movies', (req, res) => {
  res.status(200).json(movies);
});

app.get('/api/movies/:id', (req, res) => {
  const movieId = parseInt(req.params.id);
  const movie = movies.find(m => m.id === movieId);
  if (!movie) return res.status(404).json({ message: 'Movie not found' });
  res.status(200).json(movie);
});

app.post('/api/movies', (req, res) => {
  const { error, value } = movieSchema.validate(req.body);
  if (error) {
    return res.status(400).json({ error: error.details[0].message });
  }

  const newMovie = { id: movies.length ? movies[movies.length - 1].id + 1 : 1, ...value };
  movies.push(newMovie);
  res.status(201).json(newMovie);
});

app.put('/api/movies/:id', (req, res) => {
  const movieId = parseInt(req.params.id);
  const index = movies.findIndex(m => m.id === movieId);
  if (index === -1) return res.status(404).json({ message: 'Movie not found' });

  const { error, value } = movieSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details[0].message });

  movies[index] = { ...movies[index], ...value };
  res.status(200).json(movies[index]);
});

app.delete('/api/movies/:id', (req, res) => {
  const movieId = parseInt(req.params.id);
  const index = movies.findIndex(m => m.id === movieId);
  if (index === -1) return res.status(404).json({ message: 'Movie not found' });

  const deletedMovie = movies.splice(index, 1)[0];
  res.status(200).json({ message: 'Movie deleted successfully', movie: deletedMovie });
});

app.use((req, res) => {
  res.status(404).json({ error: 'API endpoint not found' });
});

app.listen(PORT, () => {
  console.log(`CineTrack API running at http://localhost:${PORT}`);
});
```

### Install required package
```bash
npm install express joi
```
If the package installation command above was already run during project setup, do not repeat it.

### Postman tests
- GET `http://localhost:8080/api/movies`
- GET `http://localhost:8080/api/movies/1`
- POST to `http://localhost:8080/api/movies` with JSON body
- PUT to same endpoint with updated object
- DELETE `http://localhost:8080/api/movies/1`

### Example POST body
```json
{
  "title": "Avatar",
  "genre": "Sci-Fi",
  "director": "James Cameron",
  "releaseYear": 2009,
  "rating": 8.8,
  "status": "Favourite"
}
```

### Failure backup
If Postman not available, use curl:
```bash
curl -X POST http://localhost:8080/api/movies -H "Content-Type: application/json" -d '{"title":"Avatar","genre":"Sci-Fi","director":"James Cameron","releaseYear":2009,"rating":8.8,"status":"Favourite"}'
```

---

## 6) Experiment 3: Firebase Cloud Services Integration

### Aim
Integrate Google Authentication, Firestore student CRUD, file upload to Firebase Storage, and deploy the application with Firebase Hosting.

### Useful links
- [Firebase Console](https://console.firebase.google.com/)
- [Node.js LTS download](https://nodejs.org/en/download)
- [Firebase CLI reference](https://firebase.google.com/docs/cli)
- [Firebase Web setup](https://firebase.google.com/docs/web/setup)
- [Google sign-in for web](https://firebase.google.com/docs/auth/web/google-signin)
- [Firestore web guide](https://firebase.google.com/docs/firestore/quickstart)
- [Storage web guide](https://firebase.google.com/docs/storage/web/start)
- [Firebase Hosting guide](https://firebase.google.com/docs/hosting)

### Create the project/services
1. In Firebase Console, create a project and add a **Web app**. Copy its Firebase config.
2. **Authentication -> Sign-in method -> Google -> Enable**.
3. **Firestore Database -> Create database**. Choose a region and production/locked mode.
4. **Storage -> Get started**; select the same suitable region if possible.
5. Add `localhost` under **Authentication -> Settings -> Authorized domains** if it is absent.
6. In Firestore **Rules**, publish the rules below. Repeat in Storage **Rules**.

### Create the app folder
```bash
mkdir firebase-student
cd firebase-student
npm init -y
npm install firebase
npm install --save-dev firebase-tools
npx firebase login
npx firebase init hosting
```
During `firebase init hosting`: select the project; set public directory to `public`; configure as a single-page app: **No**; do not overwrite files if prompted. Create `public/index.html` and paste the complete page below. `firebase init` creates `firebase.json` and `.firebaserc`.

### Firestore security rules
In **Firestore -> Rules**, use and publish:
```text
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /students/{studentId} {
      allow create: if request.auth != null
        && request.resource.data.ownerUid == request.auth.uid;
      allow read, delete: if request.auth != null
        && resource.data.ownerUid == request.auth.uid;
      allow update: if request.auth != null
        && resource.data.ownerUid == request.auth.uid
        && request.resource.data.ownerUid == request.auth.uid;
    }
  }
}
```

### Storage security rules
In **Storage -> Rules**, use and publish:
```text
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /student-files/{userId}/{fileName} {
      allow read, delete: if request.auth != null && request.auth.uid == userId;
      allow create, update: if request.auth != null
        && request.auth.uid == userId
        && request.resource.size < 5 * 1024 * 1024;
    }
  }
}
```
The 5 MB limit is for each upload. These rules intentionally require sign-in; do not replace them with public read/write rules.

### Complete `public/index.html`
Replace every config placeholder with values from **Project settings -> General -> Your apps -> SDK setup and configuration**. Do not include server secrets here; Firebase web config is client configuration and access is controlled by the rules above.
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Student Profile Manager</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; padding: 28px 16px; color: #242424; background: #fff; font: 16px/1.5 Arial, sans-serif; }
    main { max-width: 760px; margin: auto; }
    h1, h2 { font-weight: 600; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 16px 0; }
    label { display: block; margin: 12px 0 4px; }
    input { width: 100%; max-width: 520px; padding: 9px; border: 1px solid #aaa; border-radius: 4px; font: inherit; }
    button { margin: 12px 8px 0 0; padding: 9px 14px; color: #fff; background: #333; border: 0; border-radius: 4px; font: inherit; cursor: pointer; }
    button.secondary { color: #222; background: #eee; }
    .row { border-top: 1px solid #eee; padding: 12px 0; }
    #status { min-height: 1.5em; }
  </style>
</head>
<body>
<main>
  <h1>Student Profile Manager</h1>
  <p>Sign in, save student details, and optionally attach a file.</p>
  <section class="card">
    <button id="signIn">Sign in with Google</button>
    <button id="signOut" class="secondary" hidden>Sign out</button>
    <p id="account">Not signed in</p>
  </section>
  <section class="card">
    <h2>Student details</h2>
    <form id="studentForm">
      <input id="studentId" type="hidden">
      <label for="name">Name</label>
      <input id="name" required maxlength="80">
      <label for="email">Email</label>
      <input id="email" type="email" required maxlength="120">
      <label for="course">Course</label>
      <input id="course" required maxlength="80">
      <label for="attachment">Optional attachment (max 5 MB)</label>
      <input id="attachment" type="file">
      <button type="submit">Save profile</button>
      <button id="cancelEdit" type="button" class="secondary" hidden>Cancel edit</button>
    </form>
  </section>
  <section class="card">
    <h2>Saved profiles</h2>
    <button id="refresh" class="secondary">Refresh list</button>
    <div id="students"></div>
  </section>
  <p id="status" role="status"></p>
</main>
<script type="module">
  import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
  import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged }
    from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';
  import {
    getFirestore, collection, addDoc, getDocs, doc, updateDoc, deleteDoc, query, where
  } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';
  import { getStorage, ref, uploadBytes, getDownloadURL, deleteObject }
    from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-storage.js';

  const firebaseConfig = {
    apiKey: 'YOUR_API_KEY',
    authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
    projectId: 'YOUR_PROJECT_ID',
    storageBucket: 'YOUR_STORAGE_BUCKET',
    messagingSenderId: 'YOUR_SENDER_ID',
    appId: 'YOUR_APP_ID'
  };
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const db = getFirestore(app);
  const storage = getStorage(app);
  const provider = new GoogleAuthProvider();
  const form = document.getElementById('studentForm');
  const status = document.getElementById('status');
  let currentUser = null;

  function reportError(error) {
    console.error(error);
    status.textContent = error.message || 'The operation failed. Check the browser console.';
  }
  function clearForm() {
    form.reset();
    document.getElementById('studentId').value = '';
    document.getElementById('cancelEdit').hidden = true;
  }

  document.getElementById('signIn').onclick = async () => {
    try { await signInWithPopup(auth, provider); }
    catch (error) { reportError(error); }
  };
  document.getElementById('signOut').onclick = async () => {
    try { await signOut(auth); clearForm(); }
    catch (error) { reportError(error); }
  };
  document.getElementById('cancelEdit').onclick = clearForm;
  document.getElementById('refresh').onclick = loadStudents;

  onAuthStateChanged(auth, async user => {
    currentUser = user;
    document.getElementById('signIn').hidden = Boolean(user);
    document.getElementById('signOut').hidden = !user;
    document.getElementById('account').textContent = user ? `Signed in as ${user.email}` : 'Not signed in';
    document.getElementById('students').replaceChildren();
    if (user) await loadStudents();
  });

  async function loadStudents() {
    if (!currentUser) {
      status.textContent = 'Sign in before loading profiles.';
      return;
    }
    try {
      const q = query(collection(db, 'students'), where('ownerUid', '==', currentUser.uid));
      const snapshot = await getDocs(q);
      const list = document.getElementById('students');
      list.replaceChildren();
      snapshot.forEach(snapshotDoc => {
        const student = snapshotDoc.data();
        const row = document.createElement('div');
        row.className = 'row';
        const details = document.createElement('p');
        details.textContent = `${student.name} — ${student.email} — ${student.course}`;
        row.append(details);
        if (student.fileUrl) {
          const link = document.createElement('a');
          link.href = student.fileUrl;
          link.textContent = 'Open attachment';
          link.target = '_blank';
          link.rel = 'noreferrer';
          row.append(link);
        }
        const edit = document.createElement('button');
        edit.textContent = 'Edit';
        edit.onclick = () => {
          document.getElementById('studentId').value = snapshotDoc.id;
          document.getElementById('name').value = student.name;
          document.getElementById('email').value = student.email;
          document.getElementById('course').value = student.course;
          document.getElementById('cancelEdit').hidden = false;
        };
        const remove = document.createElement('button');
        remove.textContent = 'Delete';
        remove.className = 'secondary';
        remove.onclick = async () => {
          if (!confirm(`Delete ${student.name}'s profile?`)) return;
          try {
            await deleteDoc(doc(db, 'students', snapshotDoc.id));
            if (student.filePath) await deleteObject(ref(storage, student.filePath));
            status.textContent = 'Profile deleted.';
            await loadStudents();
          } catch (error) { reportError(error); }
        };
        row.append(edit, remove);
        list.append(row);
      });
      status.textContent = snapshot.empty ? 'No profiles saved yet.' : `Loaded ${snapshot.size} profile(s).`;
    } catch (error) { reportError(error); }
  }

  form.onsubmit = async event => {
    event.preventDefault();
    if (!currentUser) {
      status.textContent = 'Sign in before saving a profile.';
      return;
    }
    try {
      const id = document.getElementById('studentId').value;
      const data = {
        name: document.getElementById('name').value.trim(),
        email: document.getElementById('email').value.trim(),
        course: document.getElementById('course').value.trim(),
        ownerUid: currentUser.uid
      };
      const file = document.getElementById('attachment').files[0];
      if (file) {
        if (file.size > 5 * 1024 * 1024) throw new Error('Choose a file smaller than 5 MB.');
        const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, '_');
        const filePath = `student-files/${currentUser.uid}/${Date.now()}-${safeName}`;
        const storageRef = ref(storage, filePath);
        await uploadBytes(storageRef, file);
        data.filePath = filePath;
        data.fileUrl = await getDownloadURL(storageRef);
      }
      if (id) {
        await updateDoc(doc(db, 'students', id), data);
        status.textContent = 'Profile updated.';
      } else {
        await addDoc(collection(db, 'students'), { ...data, createdAt: new Date().toISOString() });
        status.textContent = 'Profile saved.';
      }
      clearForm();
      await loadStudents();
    } catch (error) { reportError(error); }
  };
</script>
</body>
</html>
```

### Test locally and deploy
```bash
npx firebase emulators:start --only hosting
```
For local testing, use `http://127.0.0.1:5000` shown in the terminal. If the Hosting emulator is not installed, deploy directly:
```bash
npx firebase deploy --only hosting
```
After deployment, open the Hosting URL printed by Firebase. Sign in, create a profile, refresh, edit, delete, and upload a small file. These are the checks for Authentication, Firestore CRUD, Storage, and Hosting.

### Common failures / recovery
- `auth/unauthorized-domain`: add the exact local hostname (`localhost` or `127.0.0.1`) to Firebase Authentication's authorized domains.
- `Missing or insufficient permissions`: publish the Firestore rules above. Ensure a signed-in user owns the record.
- Storage `unauthorized`: publish the Storage rules and confirm the Storage bucket is enabled and the rule's 5 MB limit is not exceeded.
- `storage/unknown` or bucket errors: copy `storageBucket` exactly from the web app configuration; enable Storage in the Firebase Console.
- Google popup blocked: allow pop-ups, or use a non-private browser window. For a popup-blocker alternative, Firebase supports `signInWithRedirect`.
- `firebase: command not found`: use the shown `npx firebase ...` commands from the project folder.
- Offline mode: Hosting emulator can show the saved page, but Google sign-in and cloud database/storage operations need network access. Do not claim cloud CRUD worked if the service could not be reached.

---

## 7) Experiment 4: Dropbox Storage as a Service with Express.js

### Aim
Build a small web application that uploads a local file to Dropbox, lists saved files, opens a temporary download link, and deletes a file. The Dropbox token stays on the server in `.env`; it is never sent to the browser.

### Useful links
- [Dropbox App Console](https://www.dropbox.com/developers/apps)
- [Dropbox API Explorer](https://dropbox.github.io/dropbox-api-v2-explorer/)
- [Dropbox JavaScript SDK](https://github.com/dropbox/dropbox-sdk-js)
- [Express](https://expressjs.com/en/starter/installing.html)
- [Node.js LTS download](https://nodejs.org/en/download)

### Create an app and token
1. Sign in to Dropbox App Console and create an app with **Scoped access**.
2. Choose **App folder** for a simple lab; it limits the app to its own Dropbox folder.
3. In **Permissions**, enable `files.content.read` and `files.content.write`, then submit/save.
4. In **Settings**, generate an access token for testing. Treat it like a password; do not paste it in this public sheet or commit it.
5. A test access token may expire. If API calls return 401, regenerate the token. The app folder is created automatically on first upload.

### Create project
```bash
mkdir dropbox-express
cd dropbox-express
npm init -y
npm install express dotenv dropbox multer
mkdir public
```
Create `.env`, `server.js`, and `public/index.html` as shown. Keep `.env` in the same folder as `server.js`.

### `.env`
```env
DROPBOX_ACCESS_TOKEN=paste_your_new_access_token_here
PORT=3000
```
Create `.gitignore`:
```text
node_modules/
.env
```

### Complete `server.js`
```js
require('dotenv').config();
const express = require('express');
const path = require('path');
const multer = require('multer');
const { Dropbox } = require('dropbox');

const app = express();
const port = Number(process.env.PORT) || 3000;
const token = process.env.DROPBOX_ACCESS_TOKEN;
if (!token) {
  console.error('Set DROPBOX_ACCESS_TOKEN in .env before starting the server.');
  process.exit(1);
}

const dbx = new Dropbox({ accessToken: token });
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }
});
app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/files', async (req, res) => {
  try {
    const result = await dbx.filesListFolder({ path: '' });
    res.json(result.result.entries.map(file => ({
      name: file.name,
      path: file.path_display
    })));
  } catch (error) {
    console.error('Dropbox list failed:', error);
    res.status(502).json({ error: 'Could not list Dropbox files. Check token and permissions.' });
  }
});

app.post('/api/upload', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'Choose a file first.' });
  const safeName = path.basename(req.file.originalname).replace(/[^a-zA-Z0-9._ -]/g, '_');
  if (!safeName || safeName === '.' || safeName === '..') {
    return res.status(400).json({ error: 'The file name is not valid.' });
  }
  try {
    const result = await dbx.filesUpload({
      path: `/${safeName}`,
      contents: req.file.buffer,
      mode: { '.tag': 'overwrite' }
    });
    res.status(201).json({ message: 'Upload complete.', name: result.result.name });
  } catch (error) {
    console.error('Dropbox upload failed:', error);
    res.status(502).json({ error: 'Upload failed. Check Dropbox token, permissions, and connection.' });
  }
});

app.get('/api/download', async (req, res) => {
  const filePath = typeof req.query.path === 'string' ? req.query.path : '';
  if (!filePath.startsWith('/')) return res.status(400).json({ error: 'A Dropbox file path is required.' });
  try {
    const result = await dbx.filesGetTemporaryLink({ path: filePath });
    res.json({ url: result.result.link });
  } catch (error) {
    console.error('Dropbox link failed:', error);
    res.status(502).json({ error: 'Could not create a download link for this file.' });
  }
});

app.delete('/api/files', async (req, res) => {
  const filePath = typeof req.body.path === 'string' ? req.body.path : '';
  if (!filePath.startsWith('/')) return res.status(400).json({ error: 'A Dropbox file path is required.' });
  try {
    await dbx.filesDeleteV2({ path: filePath });
    res.json({ message: 'File deleted.' });
  } catch (error) {
    console.error('Dropbox delete failed:', error);
    res.status(502).json({ error: 'Could not delete the Dropbox file.' });
  }
});

app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError && error.code === 'LIMIT_FILE_SIZE') {
    return res.status(413).json({ error: 'File is too large. The lab limit is 10 MB.' });
  }
  console.error('Unexpected server error:', error);
  res.status(500).json({ error: 'Unexpected server error.' });
});

app.listen(port, () => console.log(`Open http://localhost:${port}`));
```

### Complete `public/index.html`
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dropbox File Cabinet</title>
  <style>
    * { box-sizing: border-box; }
    body { max-width: 760px; margin: 32px auto; padding: 0 18px; color: #242424; background: #fff; font: 16px/1.5 Arial, sans-serif; }
    section { margin: 20px 0; padding: 18px; border: 1px solid #ddd; border-radius: 8px; }
    input { max-width: 100%; padding: 8px; }
    button { margin: 8px 6px 8px 0; padding: 8px 13px; color: #fff; background: #333; border: 0; border-radius: 4px; cursor: pointer; }
    button.delete { color: #222; background: #eee; }
    li { padding: 8px 0; border-bottom: 1px solid #eee; }
    #status { min-height: 1.5em; }
  </style>
</head>
<body>
  <h1>Dropbox File Cabinet</h1>
  <p>Upload, list, open, and remove files from the Dropbox app folder.</p>
  <section>
    <h2>Upload a file</h2>
    <form id="uploadForm">
      <input id="file" type="file" required>
      <button type="submit">Upload to Dropbox</button>
    </form>
    <p>Maximum size: 10 MB. A file with the same name replaces the existing file.</p>
  </section>
  <section>
    <h2>Files</h2>
    <button id="refresh" type="button">Refresh list</button>
    <ul id="files"></ul>
  </section>
  <p id="status" role="status"></p>
  <script>
    const statusLine = document.getElementById('status');
    async function request(url, options) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
      return data;
    }
    async function loadFiles() {
      try {
        const files = await request('/api/files');
        const list = document.getElementById('files');
        list.replaceChildren();
        for (const file of files) {
          const item = document.createElement('li');
          const name = document.createTextNode(file.name + ' ');
          const open = document.createElement('button');
          open.textContent = 'Open/download';
          open.onclick = async () => {
            try {
              const data = await request(`/api/download?path=${encodeURIComponent(file.path)}`);
              window.open(data.url, '_blank', 'noopener');
            } catch (error) { statusLine.textContent = error.message; }
          };
          const remove = document.createElement('button');
          remove.textContent = 'Delete';
          remove.className = 'delete';
          remove.onclick = async () => {
            if (!confirm(`Delete ${file.name}?`)) return;
            try {
              await request('/api/files', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: file.path })
              });
              statusLine.textContent = 'File deleted.';
              await loadFiles();
            } catch (error) { statusLine.textContent = error.message; }
          };
          item.append(name, open, remove);
          list.append(item);
        }
        if (!files.length) list.textContent = 'No files yet. Upload one above.';
        else statusLine.textContent = `${files.length} file(s) listed.`;
      } catch (error) { statusLine.textContent = error.message; }
    }
    document.getElementById('uploadForm').onsubmit = async event => {
      event.preventDefault();
      const file = document.getElementById('file').files[0];
      if (!file) return;
      if (file.size > 10 * 1024 * 1024) {
        statusLine.textContent = 'Choose a file smaller than 10 MB.';
        return;
      }
      const form = new FormData();
      form.append('file', file);
      statusLine.textContent = 'Uploading...';
      try {
        const result = await request('/api/upload', { method: 'POST', body: form });
        statusLine.textContent = result.message;
        event.target.reset();
        await loadFiles();
      } catch (error) { statusLine.textContent = error.message; }
    };
    document.getElementById('refresh').onclick = loadFiles;
    loadFiles();
  </script>
</body>
</html>
```

### Run and verify
```bash
node server.js
```
Open `http://localhost:3000`, select a small file, upload, refresh the listing, open/download it, then delete it. Verify in the Dropbox app folder in Dropbox as an independent check.

### If it fails
- `DROPBOX_ACCESS_TOKEN` missing: `.env` must be beside `server.js`; restart Node after editing `.env`.
- Dropbox 401/expired token: generate a fresh development token in App Console and update `.env`.
- Dropbox 403/insufficient permissions: enable and submit both `files.content.read` and `files.content.write`; generate a token after saving permissions.
- `Cannot find module 'dropbox'` or `multer`: run `npm install` in the app folder.
- `LIMIT_FILE_SIZE`: select a file below 10 MB, or adjust the limit in both Multer and the explanatory page text.
- Port busy: change `PORT=3001` in `.env` and open `http://localhost:3001`.
- If the Dropbox API is unreachable: run `node server.js` and verify the UI and local file selection; live upload/list/download requires internet and a valid Dropbox account/token.

---

## 8) Experiment 5: MongoDB Atlas with CRUD and Node.js

### Aim
Create a CodeSnipper application that saves, displays, edits, and deletes code snippets in MongoDB Atlas.

### Useful links
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [MongoDB Compass download](https://www.mongodb.com/try/download/compass) (optional visual database viewer)
- [Atlas connection guide](https://www.mongodb.com/docs/atlas/connect-your-application/)
- [Mongoose guide](https://mongoosejs.com/docs/guide.html)
- [Node.js LTS download](https://nodejs.org/en/download)

### Atlas setup
1. Create/sign in to Atlas and create a free cluster.
2. Under **Database Access**, create a database username and password. These are not necessarily your Atlas login credentials.
3. Under **Network Access**, add your current IP address.
4. Click **Connect -> Drivers**, select Node.js, and copy the connection string.
5. Replace `<username>`, `<password>`, and the cluster host. If the password has reserved URL characters, percent-encode it. Add a database name such as `codesnipper`.

### Project setup
```bash
mkdir mongodb-codesnipper
cd mongodb-codesnipper
npm init -y
npm install express mongoose dotenv
mkdir public
```

### `.env`
Put `.env` beside `server.js`. Never publish it.
```env
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxxx.mongodb.net/codesnipper?retryWrites=true&w=majority
PORT=5000
```
Create `.gitignore`:
```text
node_modules/
.env
```

### Complete `server.js`
```js
require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const path = require('path');

const app = express();
app.use(express.json());
const port = Number(process.env.PORT) || 5000;
app.use(express.static(path.join(__dirname, 'public')));

const snippetSchema = new mongoose.Schema({
  title: { type: String, required: true, trim: true, maxlength: 100 },
  language: { type: String, required: true, trim: true, maxlength: 40 },
  code: { type: String, required: true, maxlength: 50000 },
  createdAt: { type: Date, default: Date.now }
});
const Snippet = mongoose.model('Snippet', snippetSchema);

app.get('/api/snippets', async (req, res, next) => {
  try {
    res.json(await Snippet.find().sort({ createdAt: -1 }));
  } catch (error) { next(error); }
});

app.get('/api/snippets/:id', async (req, res, next) => {
  try {
    const snippet = await Snippet.findById(req.params.id);
    if (!snippet) return res.status(404).json({ error: 'Snippet not found.' });
    res.json(snippet);
  } catch (error) { next(error); }
});

app.post('/api/snippets', async (req, res, next) => {
  try {
    const snippet = await Snippet.create({
      title: req.body.title,
      language: req.body.language,
      code: req.body.code
    });
    res.status(201).json(snippet);
  } catch (error) { next(error); }
});

app.put('/api/snippets/:id', async (req, res, next) => {
  try {
    const snippet = await Snippet.findByIdAndUpdate(req.params.id, {
      title: req.body.title,
      language: req.body.language,
      code: req.body.code
    }, { new: true, runValidators: true });
    if (!snippet) return res.status(404).json({ error: 'Snippet not found.' });
    res.json(snippet);
  } catch (error) { next(error); }
});

app.delete('/api/snippets/:id', async (req, res, next) => {
  try {
    const snippet = await Snippet.findByIdAndDelete(req.params.id);
    if (!snippet) return res.status(404).json({ error: 'Snippet not found.' });
    res.json({ message: 'Snippet deleted.', snippet });
  } catch (error) { next(error); }
});

app.use((error, req, res, next) => {
  console.error(error);
  if (error.name === 'ValidationError') {
    return res.status(400).json({ error: error.message });
  }
  if (error.name === 'CastError') {
    return res.status(400).json({ error: 'Invalid snippet ID.' });
  }
  res.status(500).json({ error: 'Server error. Check the server terminal.' });
});

async function start() {
  if (!process.env.MONGODB_URI) throw new Error('MONGODB_URI is missing from .env');
  await mongoose.connect(process.env.MONGODB_URI, { serverSelectionTimeoutMS: 10000 });
  console.log('Connected to MongoDB Atlas.');
  app.listen(port, () => console.log(`Open http://localhost:${port}`));
}
start().catch(error => {
  console.error('MongoDB startup failed:', error.message);
  process.exit(1);
});
```

### Complete `public/index.html`
```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CodeSnipper</title>
  <style>
    * { box-sizing: border-box; }
    body { max-width: 850px; margin: 30px auto; padding: 0 18px; color: #242424; background: #fff; font: 16px/1.5 Arial, sans-serif; }
    section, article { border: 1px solid #ddd; border-radius: 8px; padding: 18px; margin: 16px 0; }
    label { display: block; margin: 10px 0 4px; }
    input, textarea { width: 100%; padding: 9px; border: 1px solid #aaa; border-radius: 4px; font: inherit; }
    textarea { min-height: 130px; font-family: Consolas, monospace; }
    button { margin: 10px 8px 0 0; padding: 8px 13px; color: #fff; background: #333; border: 0; border-radius: 4px; cursor: pointer; }
    button.secondary { color: #222; background: #eee; }
    pre { overflow-x: auto; padding: 12px; background: #f6f6f6; white-space: pre-wrap; }
    #status { min-height: 1.5em; }
  </style>
</head>
<body>
  <h1>CodeSnipper</h1>
  <p>Save and manage code snippets in MongoDB Atlas.</p>
  <section>
    <h2 id="formHeading">Add a snippet</h2>
    <form id="snippetForm">
      <input id="snippetId" type="hidden">
      <label for="title">Title</label>
      <input id="title" required maxlength="100">
      <label for="language">Language</label>
      <input id="language" required maxlength="40" placeholder="JavaScript, Java, Python...">
      <label for="code">Code</label>
      <textarea id="code" required maxlength="50000"></textarea>
      <button type="submit">Save snippet</button>
      <button id="cancel" type="button" class="secondary" hidden>Cancel edit</button>
    </form>
  </section>
  <section>
    <h2>Saved snippets</h2>
    <button id="refresh" type="button" class="secondary">Refresh</button>
    <div id="output"></div>
  </section>
  <p id="status" role="status"></p>
  <script>
    const form = document.getElementById('snippetForm');
    const statusLine = document.getElementById('status');
    async function api(url, options = {}) {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
      return data;
    }
    function clearForm() {
      form.reset();
      document.getElementById('snippetId').value = '';
      document.getElementById('formHeading').textContent = 'Add a snippet';
      document.getElementById('cancel').hidden = true;
    }
    async function loadSnippets() {
      try {
        const snippets = await api('/api/snippets');
        const output = document.getElementById('output');
        output.replaceChildren();
        if (!snippets.length) output.textContent = 'No snippets saved yet.';
        for (const snippet of snippets) {
          const card = document.createElement('article');
          const heading = document.createElement('h3');
          heading.textContent = `${snippet.title} (${snippet.language})`;
          const code = document.createElement('pre');
          code.textContent = snippet.code;
          const edit = document.createElement('button');
          edit.textContent = 'Edit';
          edit.onclick = () => {
            document.getElementById('snippetId').value = snippet._id;
            document.getElementById('title').value = snippet.title;
            document.getElementById('language').value = snippet.language;
            document.getElementById('code').value = snippet.code;
            document.getElementById('formHeading').textContent = 'Edit snippet';
            document.getElementById('cancel').hidden = false;
            window.scrollTo({ top: 0, behavior: 'smooth' });
          };
          const remove = document.createElement('button');
          remove.textContent = 'Delete';
          remove.className = 'secondary';
          remove.onclick = async () => {
            if (!confirm(`Delete "${snippet.title}"?`)) return;
            try {
              await api(`/api/snippets/${snippet._id}`, { method: 'DELETE' });
              statusLine.textContent = 'Snippet deleted.';
              await loadSnippets();
            } catch (error) { statusLine.textContent = error.message; }
          };
          card.append(heading, code, edit, remove);
          output.append(card);
        }
      } catch (error) { statusLine.textContent = error.message; }
    }
    form.onsubmit = async event => {
      event.preventDefault();
      const id = document.getElementById('snippetId').value;
      const body = {
        title: document.getElementById('title').value.trim(),
        language: document.getElementById('language').value.trim(),
        code: document.getElementById('code').value
      };
      try {
        await api(id ? `/api/snippets/${id}` : '/api/snippets', {
          method: id ? 'PUT' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        statusLine.textContent = id ? 'Snippet updated.' : 'Snippet created.';
        clearForm();
        await loadSnippets();
      } catch (error) { statusLine.textContent = error.message; }
    };
    document.getElementById('cancel').onclick = clearForm;
    document.getElementById('refresh').onclick = loadSnippets;
    loadSnippets();
  </script>
</body>
</html>
```

### Run and test
Create `public` folder and save the page above as `public/index.html`.
```bash
node server.js
```
Open `http://localhost:5000`; create, refresh, edit, then delete a snippet. API-only backup: `GET http://localhost:5000/api/snippets` in a browser or Postman.

### If it fails
- `MONGODB_URI is missing`: check `.env` name/location; ensure it is not accidentally `.env.txt`; restart the server after edits.
- `bad auth` / authentication failed: use the **Database Access** username/password, not the Atlas website login. URL-encode reserved characters in the password.
- `querySrv ENOTFOUND` / server selection timed out: check the full Atlas hostname, network connection, and Atlas **Network Access** allowlist.
- `IP not in access list`: add your current public IP in Atlas, wait for it to become active, and retry. Avoid `0.0.0.0/0` except a brief isolated test.
- `Cannot find module`: run `npm install` in the project directory.
- `Failed to fetch`: keep the Node server running and open the page from `http://localhost:5000`, not by opening the HTML file directly.
- Atlas is unreachable: keep the same API/UI, but explain the cloud connection is unverified. A local MongoDB server can be used as a practice fallback by setting `MONGODB_URI=mongodb://127.0.0.1:27017/codesnipper`.

---

## 9) Experiment 6: Auth0 SSO Implementation

### Aim
Use Auth0 as an identity provider for a React SPA, demonstrate sign-in/profile/sign-out, and send an access token to a protected Express API. Multiple apps configured in the same Auth0 tenant can reuse the browser's Auth0 SSO session.

### Useful links
- [Auth0 Dashboard](https://manage.auth0.com/)
- [Auth0 React quickstart](https://auth0.com/docs/quickstart/spa/react)
- [Auth0 API quickstart](https://auth0.com/docs/quickstart/backend/nodejs)
- [Node.js LTS download](https://nodejs.org/en/download)

### Configure Auth0
1. In Auth0 Dashboard, create an **Application -> Single Page Application**.
2. Note its **Domain** and **Client ID**. Never put a client secret in React.
3. Under **APIs**, create an API with identifier `https://api.local` and signing algorithm **RS256**.
4. In SPA settings, add and save:
   - Allowed Callback URLs: `http://localhost:5173`
   - Allowed Logout URLs: `http://localhost:5173`
   - Allowed Web Origins: `http://localhost:5173`
5. For a second SPA, create another application in the same tenant and add that app's exact localhost URLs in its settings.

### Create React SPA
```bash
npm create vite@latest auth0-spa -- --template react
cd auth0-spa
npm install
npm install @auth0/auth0-react
```
Create `.env.local` at the project root:
```env
VITE_AUTH0_DOMAIN=YOUR_TENANT_REGION.auth0.com
VITE_AUTH0_CLIENT_ID=YOUR_SPA_CLIENT_ID
VITE_AUTH0_AUDIENCE=https://api.local
```
Restart Vite after editing the env file. Use the tenant **Domain** without `https://`.

### `src/main.jsx`
```jsx
import ReactDOM from 'react-dom/client';
import App from './App';
import { Auth0Provider } from '@auth0/auth0-react';
import './style.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <Auth0Provider
    domain={import.meta.env.VITE_AUTH0_DOMAIN}
    clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
    authorizationParams={{
      redirect_uri: window.location.origin,
      audience: import.meta.env.VITE_AUTH0_AUDIENCE,
      scope: 'openid profile email'
    }}
  >
    <App />
  </Auth0Provider>
);
```

### `src/App.jsx`
```jsx
import { useAuth0 } from '@auth0/auth0-react';

function App() {
  const { loginWithRedirect, logout, user, isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();

  async function callApi() {
    const output = document.getElementById('apiResult');
    try {
      const token = await getAccessTokenSilently();
      const response = await fetch('http://localhost:4000/api/profile', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `API returned ${response.status}`);
      output.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
      output.textContent = error.message;
    }
  }

  if (isLoading) return <p>Loading...</p>;
  return (
    <main className="card">
      <h1>Auth0 SSO Lab</h1>
      {isAuthenticated ? (
        <>
          <h2>Welcome, {user.name}</h2>
          <p>{user.email}</p>
          <button onClick={callApi}>Call protected API</button>
          <button className="secondary" onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}>
            Sign out
          </button>
        </>
      ) : <button onClick={() => loginWithRedirect()}>Sign in</button>}
      <pre id="apiResult" aria-live="polite"></pre>
    </main>
  );
}

export default App;
```

### `src/style.css`
```css
* { box-sizing: border-box; }
body { margin: 0; padding: 30px 16px; color: #242424; background: #fff; font: 16px/1.5 Arial, sans-serif; }
.card { max-width: 620px; margin: 30px auto; padding: 24px; border: 1px solid #ddd; border-radius: 8px; }
button { margin: 8px 8px 8px 0; padding: 9px 14px; color: #fff; background: #333; border: 0; border-radius: 4px; cursor: pointer; }
button.secondary { color: #222; background: #eee; }
pre { min-height: 28px; overflow-x: auto; padding: 12px; background: #f5f5f5; white-space: pre-wrap; }
```

### Optional protected API
Create `api/server.js`:
```js
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { auth } = require('express-oauth2-jwt-bearer');

const app = express();
const domain = process.env.AUTH0_DOMAIN;
const audience = process.env.AUTH0_AUDIENCE;
if (!domain || !audience) throw new Error('Set AUTH0_DOMAIN and AUTH0_AUDIENCE in api/.env');
app.use(cors({ origin: 'http://localhost:5173' }));
const checkJwt = auth({ audience, issuerBaseURL: `https://${domain}/` });

app.get('/api/profile', checkJwt, (req, res) => {
  res.json({ message: 'Access token verified', subject: req.auth.payload.sub });
});
app.listen(4000, () => console.log('Protected API running at http://localhost:4000'));
```
Create the folder first if it does not exist: run `mkdir api` from the React project root.
Create `api/.env` with the same tenant and API values:
```env
AUTH0_DOMAIN=YOUR_TENANT_REGION.auth0.com
AUTH0_AUDIENCE=https://api.local
```
From the `api` folder run `npm init -y`, then:
```bash
npm install express cors dotenv express-oauth2-jwt-bearer
node server.js
```
Start React in a second terminal from `auth0-spa`:
```bash
npm run dev
```
Open `http://localhost:5173`, sign in, view the profile, click **Call protected API**, then sign out.

### Test SSO across apps
Run the second SPA on another port/origin, add that exact origin to its Auth0 callback/logout/web-origin allowlists, and test both in the same browser profile. The tenant session can avoid asking for credentials again; each app still has its own client configuration and token.

### If it fails
- `Callback URL mismatch`: add the exact Vite URL to all three allowlists and save.
- `invalid_client`: check domain and SPA client ID; never use a client secret in browser code.
- API 401: confirm the API identifier exactly matches both audience values, then sign in again to obtain a new token.
- CORS error: run API on port 4000 and set its allowed origin to the actual SPA URL.
- Missing dependency: run `npm install` in the folder for that app.
- Offline: the React layout can be shown locally, but Auth0 sign-in and JWT verification need a reachable Auth0 tenant. Do not use a fake token as proof of authentication.

---

## 11) Experiment 8: Hadoop and MapReduce Word Count

### Aim
Install Hadoop 3.x and run a word count MapReduce job.

### Official download/reference links
- [Apache Hadoop releases](https://hadoop.apache.org/releases.html) (choose Hadoop 3.x; the commands below use 3.3.6)
- [Apache Hadoop 3.3.6 archive](https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/)
- [Eclipse Temurin JDK 11 downloads](https://adoptium.net/temurin/releases/?version=11)
- [Ubuntu Desktop download](https://ubuntu.com/download/desktop) (if the lab machine does not already provide Ubuntu; Hadoop steps below target Ubuntu/Linux, including WSL)

### Important prerequisites
Run a single-node pseudo-distributed Hadoop setup on Ubuntu/Linux. Hadoop 3.3.x is commonly run with JDK 8 or 11; use JDK 11 for this procedure. On a fresh Ubuntu install, install SSH and enable passwordless localhost SSH before starting HDFS:
```bash
sudo apt install -y openssh-server
sudo service ssh start
ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
ssh -o StrictHostKeyChecking=no localhost
exit
```

### Ubuntu commands
```bash
sudo apt update
sudo apt install -y openjdk-11-jdk
java -version
```

### Edit `.bashrc`
```bash
nano ~/.bashrc
```
Add:
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```
Then:
```bash
source ~/.bashrc
```

### Download and extract Hadoop
```bash
cd ~/Downloads
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 /usr/local/hadoop
sudo chown -R "$USER":"$USER" /usr/local/hadoop
```

### `hadoop-env.sh`
Edit the indicated file and add/set this line:
```bash
nano "$HADOOP_HOME/etc/hadoop/hadoop-env.sh"
```
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

### `core-site.xml`
Replace the contents of this file with the XML shown:
```bash
nano "$HADOOP_HOME/etc/hadoop/core-site.xml"
```
```xml
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://localhost:9000</value>
  </property>
</configuration>
```

### `hdfs-site.xml`
Replace the contents of this file with the XML shown:
```bash
nano "$HADOOP_HOME/etc/hadoop/hdfs-site.xml"
```
```xml
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>file:/usr/local/hadoop/hadoop_data/hdfs/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>file:/usr/local/hadoop/hadoop_data/hdfs/datanode</value>
  </property>
</configuration>
```

### `mapred-site.xml`
If `mapred-site.xml` does not exist, copy the template first. Then edit it:
```bash
cp "$HADOOP_HOME/etc/hadoop/mapred-site.xml.template" "$HADOOP_HOME/etc/hadoop/mapred-site.xml"
nano "$HADOOP_HOME/etc/hadoop/mapred-site.xml"
```
```xml
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
</configuration>
```

### `yarn-site.xml`
Replace the contents of this file with the XML shown:
```bash
nano "$HADOOP_HOME/etc/hadoop/yarn-site.xml"
```
```xml
<configuration>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>
</configuration>
```

### Run Hadoop
```bash
mkdir -p /usr/local/hadoop/hadoop_data/hdfs/namenode
mkdir -p /usr/local/hadoop/hadoop_data/hdfs/datanode
hdfs namenode -format
start-dfs.sh
start-yarn.sh
jps
```
For a successful pseudo-distributed start, `jps` should show NameNode, DataNode, SecondaryNameNode, ResourceManager, and NodeManager in addition to `Jps`. Open the web dashboards while daemons are running: HDFS NameNode `http://localhost:9870`, YARN ResourceManager `http://localhost:8088`.

### Put input file
```bash
mkdir -p ~/input
nano ~/input/file.txt
hdfs dfs -mkdir -p /input
hdfs dfs -put ~/input/file.txt /input/
```
If the file was already uploaded and you want to replace it:
```bash
hdfs dfs -rm -f /input/file.txt
hdfs dfs -put ~/input/file.txt /input/
```

### WordCount Java program
```java
import java.io.IOException;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class WordCount {
    public static class TokenizerMapper extends Mapper<Object, Text, Text, IntWritable> {
        private final static IntWritable one = new IntWritable(1);
        private Text word = new Text();

        public void map(Object key, Text value, Context context) throws IOException, InterruptedException {
            String[] words = value.toString().split("\\s+");
            for (String w : words) {
                word.set(w);
                context.write(word, one);
            }
        }
    }

    public static class IntSumReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
        private IntWritable result = new IntWritable();

        public void reduce(Text key, Iterable<IntWritable> values, Context context)
                throws IOException, InterruptedException {
            int sum = 0;
            for (IntWritable val : values) {
                sum += val.get();
            }
            result.set(sum);
            context.write(key, result);
        }
    }

    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "word count");
        job.setJarByClass(WordCount.class);
        job.setMapperClass(TokenizerMapper.class);
        job.setReducerClass(IntSumReducer.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
```

### Compile and run
```bash
javac -classpath $(hadoop classpath) WordCount.java
jar cf wc.jar WordCount*.class
hadoop jar wc.jar WordCount /input/file.txt /output/wc
hdfs dfs -cat /output/wc/part-r-00000
```

### Failure backups
- Format the NameNode only the first time on a new empty data directory. Formatting again erases the HDFS namespace; do not use it as a routine fix.
- If Hadoop daemons are already running, stop them before restarting:
```bash
stop-dfs.sh
stop-yarn.sh
```
- If Java mismatch: ensure `JAVA_HOME` correctly points to installed JDK.
```bash
readlink -f $(which java)
```
- If SSH asks for a password or refuses: check `sudo service ssh status`, then repeat the localhost key setup above.
- If the downloaded URL has moved, use the official Hadoop releases link and replace the version in both download URL and extracted folder.

---

## 12) Experiment 9: MPI and OpenMP Parallel Programming

### Aim
Use MPI for process-based parallelism and OpenMP for thread-based parallelism.

### Official download/reference links
- [Open MPI downloads](https://www.open-mpi.org/software/ompi/)
- [Open MPI documentation](https://docs.open-mpi.org/)
- [GCC download and documentation](https://gcc.gnu.org/)
- [Ubuntu downloads](https://ubuntu.com/download/desktop) (recommended lab environment; the package commands below are Ubuntu)

The following commands assume Ubuntu/Linux with an internet connection. If you use Windows, run them inside Ubuntu on the lab VM or WSL; native PowerShell does not provide `mpicc`.

### Install MPI
```bash
sudo apt update
sudo apt install -y build-essential openmpi-bin libopenmpi-dev
mpirun --version
```

Save the MPI source as `mpi_hello.c` in an empty working folder.

### MPI Hello World code
```c
#include <mpi.h>
#include <stdio.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    printf("Hello from process %d of %d\n", rank, size);

    MPI_Finalize();
    return 0;
}
```

### Compile and run MPI
```bash
mpicc mpi_hello.c -o mpi_hello
mpirun -np 4 ./mpi_hello
```

### OpenMP sample
Save the OpenMP source as `omp_hello.c` in the same folder.
```c
#include <omp.h>
#include <stdio.h>

int main() {
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        printf("Hello from thread %d\n", tid);
    }
    return 0;
}
```

### Compile OpenMP
```bash
gcc -fopenmp omp_hello.c -o omp_hello
./omp_hello
```

### Common OpenMP features
- `parallel` block
- `for` loop parallelism
- `reduction` for sum
- `private` / `firstprivate` / `lastprivate`
- `critical` section

### OpenMP data-sharing examples
Save this as `omp_data_sharing.c`, then compile/run with the same `gcc -fopenmp` command shown above:
```c
#include <stdio.h>
#include <omp.h>

int main(void) {
    int sharedCounter = 0;
    int lastValue = -1;
    int initialValue = 10;

    #pragma omp parallel private(sharedCounter) firstprivate(initialValue)
    {
        int threadId = omp_get_thread_num();
        sharedCounter = threadId;
        initialValue += threadId;
        printf("thread=%d private=%d firstprivate-copy=%d\n",
               threadId, sharedCounter, initialValue);
    }

    #pragma omp parallel for lastprivate(lastValue)
    for (int i = 0; i < 4; i++) {
        lastValue = i;
    }
    printf("lastprivate value after loop = %d (expected 3)\n", lastValue);

    #pragma omp parallel for
    for (int i = 0; i < 1000; i++) {
        #pragma omp critical
        sharedCounter++;
    }
    printf("critical-section counter = %d (expected 1000)\n", sharedCounter);
    return 0;
}
```
`private` variables are per-thread and must be initialized inside their region. `firstprivate` gives each thread its own copy initialized from the original value. `lastprivate` copies the value from the final logical loop iteration back to the outer variable. `critical` allows one thread at a time to update the shared counter.

### Example reduction
```c
#include <stdio.h>
#include <omp.h>

int main() {
    int sum = 0;
    int arr[10] = {1,2,3,4,5,6,7,8,9,10};

    #pragma omp parallel for reduction(+:sum)
    for (int i = 0; i < 10; i++) {
        sum += arr[i];
    }

    printf("Sum = %d\n", sum);
    return 0;
}
```

### Backup for missing MPI/OpenMP packages
```bash
sudo apt update
sudo apt install -y build-essential openmpi-bin libopenmpi-dev
```
If compilation says `mpi.h: No such file or directory`, ensure `libopenmpi-dev` is installed and compile with `mpicc` (not `gcc`). If it says `omp.h` is missing, install GCC/build-essential; `gcc -fopenmp` links OpenMP on Ubuntu. Output line ordering varies because processes/threads run concurrently.

---

## 13) Experiment 10: Apache Spark on HDFS

### Aim
Install Spark and run word count using RDDs. This lab PDF's procedure runs the job in local Spark mode over a text file; it does not actually configure HDFS. An optional HDFS input is described below.

### Official download/reference links
- [Apache Spark downloads](https://spark.apache.org/downloads.html) (choose a prebuilt package for Hadoop 3)
- [Apache Spark documentation](https://spark.apache.org/docs/latest/)
- [Eclipse Temurin JDK 17 downloads](https://adoptium.net/temurin/releases/?version=17)
- [Scala downloads](https://www.scala-lang.org/download/)

### Install Java
```bash
sudo apt update
sudo apt install -y openjdk-17-jdk
java -version
```

### Download Spark
On the download page choose a prebuilt Spark distribution for Hadoop 3; copy the exact archive link and substitute `SPARK_VERSION` and `SPARK_ARCHIVE` below. Example archive names follow `spark-<version>-bin-hadoop3.tgz`.
```bash
cd ~/Downloads
wget https://dlcdn.apache.org/spark/SPARK_VERSION/SPARK_ARCHIVE
tar -xzf SPARK_ARCHIVE
sudo mv spark-*-bin-hadoop3 /usr/local/spark
```
For example, replace `SPARK_VERSION` with the version folder shown on the official download page and `SPARK_ARCHIVE` with the complete archive filename. If Apache's mirror changes, use the download page; do not guess a version URL.

### Configure environment
```bash
nano ~/.bashrc
```
Add:
```bash
export SPARK_HOME=/usr/local/spark
export PATH=$PATH:$SPARK_HOME/bin
```
Then:
```bash
source ~/.bashrc
```

### Verify Spark
```bash
spark-shell
```
At the `scala>` prompt, type `:quit` to exit. Scala is bundled with Spark; a separate `scala` installation is usually not necessary for `spark-shell`.

### Create input file
```bash
nano input.txt
cat input.txt
```
Enter a few lines such as `cloud computing cloud lab`, save, and exit the editor. You can avoid the editor with:
```bash
printf 'cloud computing cloud lab\nspark processes data\n' > input.txt
```

### Spark word count example
At the `scala>` prompt, type these commands (not in Bash):
```scala
val inputFile = sc.textFile("input.txt")
val counts = inputFile.flatMap(line => line.split("\\s+")).map(word => (word, 1)).reduceByKey(_ + _)
counts.collect().foreach(println)
counts.saveAsTextFile("output")
```
The Spark Web UI is normally available at `http://localhost:4040` while the application is running.

### Optional: read and write through HDFS
This part requires Hadoop HDFS to be configured and running on `localhost:9000` (see Experiment 8). Upload a test input and run Spark against HDFS paths:
```bash
hdfs dfs -mkdir -p /input
hdfs dfs -put -f input.txt /input/input.txt
```
In `spark-shell`:
```scala
val hdfsInput = sc.textFile("hdfs://localhost:9000/input/input.txt")
val hdfsCounts = hdfsInput.flatMap(line => line.split("\\s+")).map(word => (word, 1)).reduceByKey(_ + _)
hdfsCounts.collect().foreach(println)
hdfsCounts.saveAsTextFile("hdfs://localhost:9000/output/spark-wordcount")
```
View it in the Linux terminal:
```bash
hdfs dfs -cat /output/spark-wordcount/part-00000
```
Remove only the generated HDFS output before another run:
```bash
hdfs dfs -rm -r /output/spark-wordcount
```

### View output
```bash
ls output
cat output/part-00000
```

### Failure backup
If `spark-shell` is not found:
```bash
export SPARK_HOME=/usr/local/spark
export PATH=$PATH:$SPARK_HOME/bin
spark-shell
```
If `output` already exists, Spark refuses to overwrite it. Before rerunning, remove only this experiment's generated output folder:
```bash
rm -r output
```
If `input.txt` is not found, start `spark-shell` from the directory containing it or use the full path, for example `sc.textFile("/home/student/input.txt")`.

---

## 14) Experiment 11A: CloudSim Installation

### Aim
Install CloudSim 5.0 in Eclipse and add Apache Commons Math libraries.

### Official download links
- [CloudSim 5.0 source/release](https://github.com/Cloudslab/cloudsim/releases)
- [CloudSim project repository](https://github.com/Cloudslab/cloudsim)
- [Apache Commons Math downloads](https://commons.apache.org/proper/commons-math/download_math.cgi)
- [Eclipse IDE downloads](https://www.eclipse.org/downloads/)
- [Eclipse Temurin JDK downloads](https://adoptium.net/temurin/releases/)

### Steps
1. Install a JDK and Eclipse. Confirm `java -version` in a terminal.
2. Download CloudSim 5.0 from Releases (or use the lab-provided archive) and extract it.
3. In Eclipse, choose **File -> Import -> General -> Existing Projects into Workspace**, select the extracted project root, then Finish. If it is not a recognized Eclipse project, use **File -> New -> Java Project** and follow the lab's source-folder instructions.
4. Right-click project -> **Properties -> Java Build Path -> Libraries**.
5. Click **Add External JARs** and add the Commons Math JAR(s) required by the CloudSim distribution. If its archive includes `jars/` or `lib/`, add the required bundled JARs as well.
6. Confirm JARs appear in **Referenced Libraries**, then **Apply and Close**.
7. Open the provided examples package and run a simple CloudSim example. A successful console run verifies the setup.

### Example import in Java project
```java
import org.cloudbus.cloudsim.*;
```

### Common issue
If project cannot compile, ensure JARs are added to the **project** build path, source files are in a source folder, and Java execution environment matches the CloudSim release.

### Backup
- Re-import the extracted project with **Existing Projects into Workspace**.
- If the prebuilt release archive is unavailable, use the source release from the official GitHub repository and follow its included build instructions.
- If Commons Math download is unavailable but its JAR is bundled in the lab archive, use that copy; avoid downloading random JARs from unofficial sites.

---

## 15) Experiment 11B: FCFS Resource Allocation in CloudSim

### Aim
Implement a simple first-come-first-serve resource allocation algorithm in CloudSim.

### Downloads and prerequisites
- [CloudSim 5.0 releases](https://github.com/Cloudslab/cloudsim/releases)
- [Apache Commons Math download](https://commons.apache.org/proper/commons-math/download_math.cgi)
- [Eclipse IDE download](https://www.eclipse.org/downloads/)

Import this class into the same CloudSim project after confirming the sample simulation there compiles and runs.

### Create Java class in package
```java
package org.cloudbus.cloudsim.examples;
```

### Working CloudSim code template
```java
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.LinkedList;
import java.util.List;

import org.cloudbus.cloudsim.Cloudlet;
import org.cloudbus.cloudsim.CloudletSchedulerTimeShared;
import org.cloudbus.cloudsim.Datacenter;
import org.cloudbus.cloudsim.DatacenterBroker;
import org.cloudbus.cloudsim.DatacenterCharacteristics;
import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Storage;
import org.cloudbus.cloudsim.UtilizationModel;
import org.cloudbus.cloudsim.UtilizationModelFull;
import org.cloudbus.cloudsim.Vm;
import org.cloudbus.cloudsim.VmAllocationPolicySimple;
import org.cloudbus.cloudsim.VmSchedulerTimeShared;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.provisioners.BwProvisionerSimple;
import org.cloudbus.cloudsim.provisioners.PeProvisionerSimple;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;

public class resourcealloc {
    private static List<Cloudlet> cloudletList;
    private static List<Vm> vmlist;

    public static void main(String[] args) {
        Log.printLine("Starting FCFS Resource Allocation...");

        try {
            int numUser = 1;
            Calendar calendar = Calendar.getInstance();
            boolean traceFlag = false;
            CloudSim.init(numUser, calendar, traceFlag);

            Datacenter datacenter = createDatacenter("Datacenter_0");
            DatacenterBroker broker = createBroker();
            int brokerId = broker.getId();

            vmlist = new ArrayList<Vm>();
            int vmCount = 4;
            for (int i = 0; i < vmCount; i++) {
                int vmid = i;
                int mips = 1000;
                long size = 10000;
                int ram = 512;
                long bw = 1000;
                int pesNumber = 1;
                String vmm = "Xen";

                Vm vm = new Vm(vmid, brokerId, mips, pesNumber, ram, bw, size, vmm,
                        new CloudletSchedulerTimeShared());
                vmlist.add(vm);
            }

            broker.submitVmList(vmlist);

            cloudletList = new ArrayList<Cloudlet>();
            int cloudletCount = 8;
            long length = 400000;
            long fileSize = 300;
            long outputSize = 300;
            UtilizationModel utilizationModel = new UtilizationModelFull();

            for (int i = 0; i < cloudletCount; i++) {
                Cloudlet cloudlet = new Cloudlet(i, length, 1, fileSize, outputSize,
                        utilizationModel, utilizationModel, utilizationModel);
                cloudlet.setUserId(brokerId);
                cloudletList.add(cloudlet);
            }

            broker.submitCloudletList(cloudletList);
            CloudSim.startSimulation();
            CloudSim.stopSimulation();

            List<Cloudlet> resultList = broker.getCloudletReceivedList();
            printCloudletList(resultList);
            Log.printLine("FCFS Resource Allocation simulation finished!");
        } catch (Exception e) {
            e.printStackTrace();
            Log.printLine("An error occurred during simulation.");
        }
    }

    private static Datacenter createDatacenter(String name) {
        List<Host> hostList = new ArrayList<Host>();

        for (int i = 0; i < 4; i++) {
            int hostId = i;
            int ram = 2048;
            long storage = 1000000;
            int bw = 10000;
            List<Pe> peList = new ArrayList<Pe>();
            peList.add(new Pe(0, new PeProvisionerSimple(1000)));

            Host host = new Host(hostId, new RamProvisionerSimple(ram),
                    new BwProvisionerSimple(bw), storage, peList,
                    new VmSchedulerTimeShared(peList));
            hostList.add(host);
        }

        String arch = "x86";
        String os = "Linux";
        String vmm = "Xen";
        double timeZone = 10.0;
        double cost = 3.0;
        double costPerMem = 0.05;
        double costPerStorage = 0.001;
        double costPerBw = 0.0;

        LinkedList<Storage> storageList = new LinkedList<Storage>();
        DatacenterCharacteristics characteristics = new DatacenterCharacteristics(
                arch, os, vmm, hostList, timeZone, cost, costPerMem, costPerStorage, costPerBw);

        Datacenter datacenter = null;
        try {
            datacenter = new Datacenter(name, characteristics, new VmAllocationPolicySimple(hostList), storageList, 0);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return datacenter;
    }

    private static DatacenterBroker createBroker() {
        DatacenterBroker broker = null;
        try {
            broker = new DatacenterBroker("Broker");
        } catch (Exception e) {
            e.printStackTrace();
        }
        return broker;
    }

    private static void printCloudletList(List<Cloudlet> list) {
        int size = list.size();
        String indent = "  ";
        Log.printLine();
        Log.printLine("========== FCFS RESOURCE ALLOCATION OUTPUT ==========");
        Log.printLine("Cloudlet ID" + indent + "STATUS" + indent + "Data center ID" + indent + "VM ID" + indent + "Time" + indent + "Start Time" + indent + "Finish Time");

        DecimalFormat dft = new DecimalFormat("###.##");

        for (int i = 0; i < size; i++) {
            Cloudlet cloudlet = list.get(i);
            Log.print(indent + cloudlet.getCloudletId() + indent + indent);

            if (cloudlet.getCloudletStatus() == Cloudlet.SUCCESS) {
                Log.print("SUCCESS");
                Log.printLine(
                    indent + indent + cloudlet.getResourceId() +
                    indent + indent + cloudlet.getVmId() +
                    indent + indent + dft.format(cloudlet.getActualCPUTime()) +
                    indent + indent + dft.format(cloudlet.getExecStartTime()) +
                    indent + indent + dft.format(cloudlet.getFinishTime())
                );
            }
        }
    }
}
```

### Additional extra-check
- If CloudSim examples do not compile, re-add the whole `commons-math` jar set and ensure you are using Java 8/11 in Eclipse.

---

## 16) Experiment 12: CloudAnalyst

### Aim
Install CloudAnalyst using NetBeans and run simulation.

### Official download links
- [CloudAnalyst ZIP from Cloudbus/University of Melbourne](http://clouds.cis.unimelb.edu.au/cloudsim/CloudAnalyst.zip)
- [CloudSim/CloudAnalyst project page](http://www.cloudbus.org/cloudsim/)
- [Apache NetBeans downloads](https://netbeans.apache.org/front/main/download/)
- [Eclipse Temurin JDK downloads](https://adoptium.net/temurin/releases/)

### Steps
1. Install a JDK and NetBeans; select a JDK-supported NetBeans installer.
2. Download the CloudAnalyst ZIP above or use the lab-provided project ZIP, then extract it.
3. In NetBeans, choose **File -> Open Project** and select the extracted project folder.
4. If asked to resolve dependencies, allow NetBeans to resolve the project libraries; inspect the downloaded archive's included instructions if dependencies are still missing.
5. Choose **Clean and Build**, then **Run Project**. The lab PDF says to ignore an error if the interface opens, but do not ignore a build failure that prevents launch; use the fixes below.
6. In the CloudAnalyst window, select **Configure Simulation**. Configure the required user bases, deployment region/data centers, VM/load-balancing settings, and simulation duration for the lab. Click **Done**.
7. Select **Run Simulation** and record the results and screenshots.

### Common issue
If the project shows a build error, check the output pane for the first actual compiler/dependency error, choose the installed JDK in **Project Properties -> Libraries**, resolve missing JAR dependencies, then Clean and Build again.

### Download/run fallback
- If the direct ZIP is unavailable, use the CloudSim/CloudAnalyst project page or the copy provided by the lab instructor.
- Avoid downloading executable JARs from third-party download portals.
- If NetBeans cannot import the project, try **File -> Open Project** on the folder that directly contains the NetBeans project metadata, not its parent folder.

---

# 17) General Lab Viva/Submission Tips

### How to write the result section
Use a fixed format:
```text
Thus, the experiment was successfully completed. The required setup, configuration, and execution were performed. The output was verified, and the expected result was achieved.
```

### How to write aim section
```text
Aim: To implement/connect/configure the required cloud service or application using the given platform and verify the output.
```

### How to explain common failure conditions
- Missing Java/Node/Python package
- Wrong PATH variable
- Firewalls or IP not allowed
- Invalid API token/key
- Port busy

### Common debugging commands
```bash
java -version
node -v
npm -v
python --version
pip --version
jps
ss -tulpn | grep -E '3000|5000|8080|9000'
```

### If port is busy
Linux/macOS:
```bash
lsof -i :3000
kill -9 <PID>
```
Windows PowerShell:
```powershell
netstat -ano | findstr :3000
Stop-Process -Id <PID>
```

---

# 18) One-Page Official Lab Template You Can Copy

```text
Aim:
To [briefly state the intended objective].

Requirements:
- Software / SDK / Service required
- Platform / environment

Procedure:
1. Install required software.
2. Configure environment variables or project settings.
3. Create or import the project.
4. Write or run the required code.
5. Execute the task and verify output.
6. Record screenshots / result.

Code / Commands:
[Paste the required code or commands here]

Output:
[Write the actual observed output]

Result:
Thus, the experiment was successfully executed and the required objective was achieved.
```

---

# 19) Final Notes

This cheat sheet reconstructs the likely working lab content from the PDFs and closes the missing gaps. For final submission, use the exact experiment name, the procedure steps, and the code templates above.

If a PDF page is partially cut off, use the closest correct standard implementation pattern shown here.

Recommended approach for the lab record:
- Keep it concise.
- Add commands and relevant code snippets.
- Add a short result paragraph.
- Include screenshots where possible.
- Use the nearest working verified template from this file.

---

Last updated: 2026-10-11
