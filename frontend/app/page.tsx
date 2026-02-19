import { redirect } from "next/navigation";

export default function Home() {
  // Automatically send user to the Login page
  redirect("/login");
}