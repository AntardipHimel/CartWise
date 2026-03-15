# CartWise — Smart Grocery List Optimizer

> Build your grocery list, compare prices across nearby stores, and find the smartest route — factoring in gas cost and drive time.

**RocketHacks 2026 | Fintech Track | Team 404BNF**

## What is CartWise?

CartWise is a grocery list optimization app. You build your shopping list, and it compares prices for every item across multiple nearby stores — different brands, sizes, and per-unit costs. Then it figures out the most cost-effective way to buy everything, including the gas you spend driving between stores.

Unlike price comparison apps that only show sticker prices, CartWise calculates the **total cost of your shopping trip** — what you pay for items plus what you spend getting there.

## Key Numbers

| Metric | Value |
|--------|-------|
| Products | 100,000 |
| Store locations | 1,000 |
| Store chains | Walmart, Kroger, Target, Costco, Trader Joe's |
| Product categories | 80+ |
| API endpoints | 12 |
| Optimization speed | Under 2 seconds |

## Tech Stack

- **Frontend:** Next.js 16, TypeScript, Tailwind CSS, Leaflet.js
- **Backend:** Python FastAPI, Motor (async MongoDB)
- **Database:** MongoDB Atlas (cloud)
- **External API:** Kroger Product API (OAuth2)

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Create `backend/.env`:
```
MONGODB_URI=mongodb+srv://ahimel:mongodb%402026@cluster0.evncqrj.mongodb.net/cartwise?retryWrites=true&w=majority
DATABASE_NAME=cartwise
KROGER_CLIENT_ID=cartwise-404bnf-bbcc0vsm
KROGER_CLIENT_SECRET=kTMJEcV4ED2ZoxwHYi0av8u53ivM45ylKqfmRI1A
```

Start the server:
```bash
python -m uvicorn app.main:app --reload
```

Verify: http://127.0.0.1:8000

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Verify: http://localhost:3000

### Seed Database (if needed)
```bash
cd backend
python -m app.seed
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/users | Create user profile |
| POST | /api/login | Authenticate |
| GET | /api/users/{email} | Get profile |
| PUT | /api/users/{email} | Update settings |
| GET | /api/items/suggest?q=ri | Autocomplete search |
| GET | /api/items/{key}/filters | Available brands/sizes |
| POST | /api/candidates/build | Build candidate products |
| POST | /api/optimize-smart | Run route optimization |
| GET | /api/stores | List stores |
| GET | /api/products | List products |
| POST | /api/users/{email}/trips | Save trip |
| GET | /api/users/{email}/recommendations | Get suggestions |

## How the Optimizer Works

1. **Pre-filter** 1,000 stores to only nearby, open ones with matching products (~15)
2. **Quick-score** each store combination to prune bad ones early
3. **Evaluate** remaining combos — assign items to cheapest stores
4. **Route** using nearest-neighbor (O(n²) instead of O(n!) permutations)
5. **Compare** Cheapest Route vs Shortest Route and recommend the better option

**Cost formula:** Total = item prices + (drive distance / MPG × gas price)

## Team

| Member | Role |
|--------|------|
| Ronit Dey | Backend & Algorithm |
| Azahar Alam | Frontend & UI |
| Antardip Himel | Data & Architecture |

University of Toledo — RocketHacks 2026