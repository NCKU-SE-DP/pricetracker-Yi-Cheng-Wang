<template>
    <nav class="navbar" :style="{ height: menuOpen ? 'auto' : '4.5em' }">
        <div class="navbar-header">
            <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
            <div class="hamburger" @click="toggleMenu">
                &#9776;
            </div>
        </div>
        <ul class="options" :style="{ display: menuOpen || isLargeScreen ? 'flex' : 'none' }">
            <li @click="toggleMenu"><RouterLink to="/overview">物價概覽</RouterLink></li>
            <li @click="toggleMenu"><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <li @click="toggleMenu"><RouterLink to="/news">相關新聞</RouterLink></li>
            <li v-if="!isLoggedIn" @click="toggleMenu"><RouterLink to="/login">登入</RouterLink></li>
            <li v-else @click="logout,toggleMenu">Hi, {{getUserName}}! 登出</li>
        </ul>
    </nav>
</template>

<script>
import { useAuthStore } from '@/stores/auth';

export default {
    name: 'NavBar',
    data() {
        return {
            menuOpen: false,
            isLargeScreen: window.innerWidth > 768
        };
    },
    computed: {
        isLoggedIn() {
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName() {
            const userStore = useAuthStore();
            return userStore.getUserName;
        }
    },
    methods: {
        toggleMenu() {
            this.menuOpen = !this.menuOpen;
        },
        logout() {
            const userStore = useAuthStore();
            userStore.logout();
        },
        handleResize() {
            this.isLargeScreen = window.innerWidth > 768;
            if (this.isLargeScreen) {
                this.menuOpen = true;
            } else {
                this.menuOpen = false;
            }
        }
    },
    mounted() {
        window.addEventListener('resize', this.handleResize);
        this.handleResize();
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleResize);
    }
};
</script>

<style scoped>
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #f3f3f3;
    padding: 1.5em;
    width: 100%;
    align-items: center;
    box-shadow: 0 0 5px #000000;
    transition: height 0.3s ease;
}

.navbar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 40%;
}

.hamburger {
    display: none;
    font-size: 1.5em;
    cursor: pointer;
}

.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
}

.title > a{
    font-size: 1.6em;
    font-weight: bold;
    color: #2c3e50 !important;
}

.navbar li {
    color: #575B5D;
    margin: 0 .5em;
    font-size: 1.2em;
}

.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}

@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding-bottom: 0;
    }

    .navbar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }

    .title {
        align-self: flex-start;
        margin-left: 1em;
    }

    .title > a {
        font-size: 1.4em;
    }

    .hamburger {
        align-self: flex-end;
        display: block;
    }

    .navbar .options {
        display: flex;
        flex-direction: column;
        margin-top: 10px;
        border-top: 1px solid #ddd;
        padding-top: 10px;
        width: 100%;
        transition: all 0.3s ease;
    }

    .navbar .options li {
        margin-left: 0;
        margin-bottom: 10px;
        border-bottom: 1px solid #ddd;
        padding: 5px 0;
        width: 100%;
    }

    .navbar .options li:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }

    body {
        min-width: 600px;
    }
}
</style>