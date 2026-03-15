import Link from "next/link";
import UserCreateForm from "@/components/UserCreateForm";

export default function CreateUserPage() {
  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="mx-auto max-w-4xl px-4 py-10">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-emerald-400">CartWise</h1>
            <p className="mt-2 text-gray-400">
              Create a shopper profile for grocery optimization.
            </p>
          </div>

          <Link
            href="/"
            className="rounded-xl border border-gray-700 px-4 py-3 text-sm font-medium text-gray-300 transition hover:border-emerald-500 hover:text-emerald-400"
          >
            Back to Home
          </Link>
        </div>

        <UserCreateForm />
      </div>
    </main>
  );
}