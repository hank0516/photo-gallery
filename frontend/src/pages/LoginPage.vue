<template>
  <div class="login-page">
    <div class="login-card">
      <h1>Photo Gallery</h1>

      <template v-if="!authStore.isLoggedIn">
        <p>A private photo gallery. Sign in to continue.</p>
        <a href="/api/photo-gallery/auth/login" class="btn-google">
          <img src="https://www.google.com/favicon.ico" alt="" width="18" />
          Sign in with Google
        </a>
      </template>

      <template v-else>
        <p class="pending">
          Welcome, {{ authStore.user.name }}.<br />
          Your account is pending access. Please ask an admin to grant you access.
        </p>
        <button @click="authStore.logout()">Sign out</button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
const authStore = useAuthStore()
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f5f5;
}
.login-card {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,.08);
  text-align: center;
  max-width: 360px;
  width: 100%;
}
h1 { margin-bottom: 0.5rem; font-size: 1.8rem; }
p  { color: #555; margin-bottom: 1.5rem; }
.btn-google {
  display: inline-flex;
  align-items: center;
  gap: .6rem;
  padding: .75rem 1.5rem;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  text-decoration: none;
  color: #333;
  cursor: pointer;
}
.btn-google:hover { background: #f8f8f8; }
.pending { color: #c47900; }
button {
  padding: .6rem 1.2rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  background: white;
}
</style>
