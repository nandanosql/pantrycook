import { createRouter, createWebHistory } from "vue-router";
import SuggestView from "./views/SuggestView.vue";
import PantryView from "./views/PantryView.vue";
import RecipesView from "./views/RecipesView.vue";
import SettingsView from "./views/SettingsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "tonight", component: SuggestView },
    { path: "/pantry", name: "pantry", component: PantryView },
    { path: "/recipes", name: "recipes", component: RecipesView },
    { path: "/settings", name: "settings", component: SettingsView },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});
