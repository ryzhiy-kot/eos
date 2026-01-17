[[Elyon]]
<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Clock Search and Add Modal | Financial Terminal</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#13c8ec",
                        "background-light": "#f6f8f8",
                        "background-dark": "#101f22",
                        "terminal-gray": "#234248",
                        "terminal-dark": "#111f22",
                    },
                    fontFamily: {
                        "display": ["Space Grotesk", "sans-serif"]
                    },
                    borderRadius: {
                        "DEFAULT": "0.125rem",
                        "lg": "0.25rem",
                        "xl": "0.5rem",
                        "full": "0.75rem"
                    },
                },
            },
        }
    </script>
<style>
        body {
            font-family: 'Space Grotesk', sans-serif;
            -webkit-font-smoothing: antialiased;
        }
        .modal-glow {
            box-shadow: 0 0 20px rgba(19, 200, 236, 0.15);
        }
        .blur-backdrop {
            backdrop-filter: blur(8px);
        }
    </style>
</head>
<body class="bg-background-light dark:bg-background-dark text-white overflow-hidden h-screen font-display">
<!-- Background Dashboard (Dimmed/Blurred) -->
<div class="fixed inset-0 z-0 flex flex-col pointer-events-none opacity-40 blur-sm grayscale-[0.5]">
<!-- Top Navigation -->
<header class="flex items-center justify-between border-b border-terminal-gray px-10 py-3 bg-terminal-dark">
<div class="flex items-center gap-8">
<div class="flex items-center gap-4 text-white">
<div class="size-6 text-primary">
<span class="material-symbols-outlined text-3xl">terminal</span>
</div>
<h2 class="text-white text-lg font-bold tracking-[-0.015em] uppercase">Financial Terminal</h2>
</div>
<div class="flex items-center gap-9 opacity-50">
<a class="text-white text-sm font-medium" href="#">Dashboard</a>
<a class="text-white text-sm font-medium border-b-2 border-primary" href="#">Markets</a>
<a class="text-white text-sm font-medium" href="#">Clocks</a>
<a class="text-white text-sm font-medium" href="#">Settings</a>
</div>
</div>
<div class="size-10 rounded-full bg-terminal-gray overflow-hidden">
<img alt="Profile" data-alt="User profile avatar placeholder" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAeqjTJSuYg05jLbW-gXEEu78ZAHMCaJdbFKPxGYCodke4D1GVSndr6xU1dubZ7JGqqQFh6D9J1RYK6oyK7KUPERvLrAY9pHKGwk4NAzoAnF_ZNxCN3jcCczk04hS0_dLfAUkvZICv6DlyoNx8FixocqEiAoXnyJuO_Q9MT61vk5kW8FrgvW0j2CrgWxiFTUg4YlJbInIz7d62DEUnavK8TWbPUBp5iynnxOGUYHZ-r9qOV84nxi-Zep4W93l9pdykqaHdI8Kwif0PR"/>
</div>
</header>
<!-- Main Workspace (Clock Grid) -->
<main class="flex-1 p-10 grid grid-cols-3 gap-6">
<!-- London Clock -->
<div class="bg-terminal-dark border border-terminal-gray p-6 flex flex-col justify-between">
<div>
<h3 class="text-primary text-xs font-bold tracking-widest uppercase mb-1">LON / LSE</h3>
<p class="text-4xl font-light">08:42:12</p>
</div>
<div class="text-[#92c0c9] text-xs">UTC +00:00 • BST</div>
</div>
<!-- New York Clock -->
<div class="bg-terminal-dark border border-terminal-gray p-6 flex flex-col justify-between">
<div>
<h3 class="text-primary text-xs font-bold tracking-widest uppercase mb-1">NYC / NYSE</h3>
<p class="text-4xl font-light">03:42:12</p>
</div>
<div class="text-[#92c0c9] text-xs">UTC -05:00 • EST</div>
</div>
<!-- Tokyo Clock -->
<div class="bg-terminal-dark border border-terminal-gray p-6 flex flex-col justify-between">
<div>
<h3 class="text-primary text-xs font-bold tracking-widest uppercase mb-1">TYO / TSE</h3>
<p class="text-4xl font-light">17:42:12</p>
</div>
<div class="text-[#92c0c9] text-xs">UTC +09:00 • JST</div>
</div>
<!-- Placeholder Map -->
<div class="col-span-3 h-64 bg-terminal-dark border border-terminal-gray overflow-hidden relative">
<div class="absolute inset-0 opacity-20">
<img alt="Map" class="w-full h-full object-cover grayscale" data-alt="Technical global map showing market connectivity" data-location="Global Market Map" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCBFggup5UHt72X2gKQpkMOBSZKhdzCN_6AstKf2OA0c-CFnMOR5r-97pBD4I9zwAs52XRL2M7xkKkfyYyKg8TvfeLkr1MRYg4otUEOdGAZPUOxEK7tjTah4o5aT1fQUC-Tr6DGb5BlSPxMqeAox4Slfy2ofC2UGvk1IHvt-wvcLGckB7VqZHYSjlhLNXwsOQ4USmFOuX7jgadNSnzzn6r-8P2cTSJeQ-M2cgSbTgTkja8HLZU-PaStS5GVQvaAf0LC0PETC4n6ulCz"/>
</div>
</div>
</main>
</div>
<!-- Modal Overlay Backdrop -->
<div class="fixed inset-0 z-10 bg-black/60 blur-backdrop flex items-center justify-center p-4">
<!-- Search/Add Modal -->
<div class="w-full max-w-[640px] bg-[#1a1d21] border border-terminal-gray modal-glow flex flex-col overflow-hidden shadow-2xl">
<!-- Modal Header -->
<div class="px-6 py-4 border-b border-terminal-gray flex items-center justify-between">
<h2 class="text-white text-sm font-bold tracking-widest uppercase">Add World Clock</h2>
<div class="text-xs text-[#92c0c9] bg-terminal-gray/50 px-2 py-1 border border-terminal-gray">CMD + K</div>
</div>
<!-- Command Search Bar -->
<div class="px-6 py-5">
<label class="flex flex-col w-full group">
<div class="flex w-full items-center rounded bg-terminal-dark border border-terminal-gray group-focus-within:border-primary transition-colors h-14">
<div class="text-primary px-4 flex items-center justify-center">
<span class="material-symbols-outlined">search</span>
</div>
<input autofocus="" class="flex-1 bg-transparent border-none text-white text-lg font-medium placeholder:text-[#4a5f63] focus:ring-0 px-2" placeholder="Type a city or timezone (e.g. Singapore, EST)..." value="Singapore"/>
<div class="px-4 text-[#92c0c9]">
<button class="hover:text-white flex items-center">
<span class="material-symbols-outlined text-xl">cancel</span>
</button>
</div>
</div>
</label>
</div>
<!-- Results List -->
<div class="flex-1 overflow-y-auto max-h-[400px] border-t border-terminal-gray/30">
<!-- Result Item: Selected State -->
<div class="flex items-center gap-4 bg-primary/10 px-6 py-4 justify-between group cursor-pointer relative">
<div class="absolute left-0 top-0 bottom-0 w-1 bg-primary"></div>
<div class="flex items-center gap-4">
<div class="text-primary flex items-center justify-center rounded-lg bg-primary/20 shrink-0 size-12 border border-primary/30">
<span class="material-symbols-outlined">globe</span>
</div>
<div class="flex flex-col">
<p class="text-white text-base font-bold leading-none mb-1">Singapore, Singapore</p>
<p class="text-primary text-xs font-mono tracking-tight">SGT, UTC +8:00 • <span class="text-[#92c0c9]">16:42 PM</span></p>
</div>
</div>
<div class="shrink-0">
<button class="text-xs font-bold text-primary uppercase bg-primary/20 px-3 py-1.5 border border-primary/40 rounded tracking-wider">
                            [ENTER] to Add
                        </button>
</div>
</div>
<!-- Result Item 2 -->
<div class="flex items-center gap-4 hover:bg-terminal-gray/30 px-6 py-4 justify-between group cursor-pointer border-t border-terminal-gray/10">
<div class="flex items-center gap-4">
<div class="text-[#92c0c9] flex items-center justify-center rounded-lg bg-terminal-gray/50 shrink-0 size-12 border border-terminal-gray">
<span class="material-symbols-outlined">location_city</span>
</div>
<div class="flex flex-col">
<p class="text-white text-base font-medium leading-none mb-1">Sinnamary, French Guiana</p>
<p class="text-[#92c0c9] text-xs font-mono tracking-tight">SRT, UTC -3:00 • <span class="opacity-70">05:42 AM</span></p>
</div>
</div>
<div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="text-xs font-bold text-[#92c0c9] uppercase bg-terminal-gray px-3 py-1.5 border border-terminal-gray rounded tracking-wider">
                            Add
                        </button>
</div>
</div>
<!-- Result Item 3 -->
<div class="flex items-center gap-4 hover:bg-terminal-gray/30 px-6 py-4 justify-between group cursor-pointer border-t border-terminal-gray/10">
<div class="flex items-center gap-4">
<div class="text-[#92c0c9] flex items-center justify-center rounded-lg bg-terminal-gray/50 shrink-0 size-12 border border-terminal-gray">
<span class="material-symbols-outlined">public</span>
</div>
<div class="flex flex-col">
<p class="text-white text-base font-medium leading-none mb-1">Sinoe, Liberia</p>
<p class="text-[#92c0c9] text-xs font-mono tracking-tight">GMT, UTC +0:00 • <span class="opacity-70">08:42 AM</span></p>
</div>
</div>
<div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="text-xs font-bold text-[#92c0c9] uppercase bg-terminal-gray px-3 py-1.5 border border-terminal-gray rounded tracking-wider">
                            Add
                        </button>
</div>
</div>
</div>
<!-- Modal Footer / Shortcuts -->
<div class="bg-terminal-dark/80 px-6 py-3 border-t border-terminal-gray flex items-center justify-between text-[#8A94A0]">
<div class="flex gap-4">
<div class="flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase">
<span class="px-1.5 py-0.5 bg-terminal-gray rounded border border-[#3a545a] text-white">ENTER</span>
<span>Select</span>
</div>
<div class="flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase">
<span class="px-1.5 py-0.5 bg-terminal-gray rounded border border-[#3a545a] text-white">↑↓</span>
<span>Navigate</span>
</div>
</div>
<div class="flex items-center gap-1.5 text-[10px] font-bold tracking-widest uppercase">
<span class="px-1.5 py-0.5 bg-terminal-gray rounded border border-[#3a545a] text-white">ESC</span>
<span>Dismiss</span>
</div>
</div>
</div>
</div>
</body></html>