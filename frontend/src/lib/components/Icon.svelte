<script lang="ts">
	import Apple from '@lucide/svelte/icons/apple';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Briefcase from '@lucide/svelte/icons/briefcase';
	import Check from '@lucide/svelte/icons/check';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import Church from '@lucide/svelte/icons/church';
	import Compass from '@lucide/svelte/icons/compass';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import Globe from '@lucide/svelte/icons/globe';
	import GraduationCap from '@lucide/svelte/icons/graduation-cap';
	import HeartPulse from '@lucide/svelte/icons/heart-pulse';
	import House from '@lucide/svelte/icons/house';
	import Info from '@lucide/svelte/icons/info';
	import Languages from '@lucide/svelte/icons/languages';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import Phone from '@lucide/svelte/icons/phone';
	import Printer from '@lucide/svelte/icons/printer';
	import Scale from '@lucide/svelte/icons/scale';
	import Search from '@lucide/svelte/icons/search';
	import Share2 from '@lucide/svelte/icons/share-2';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import Siren from '@lucide/svelte/icons/siren';
	import X from '@lucide/svelte/icons/x';

	const ICONS = {
		apple: Apple,
		'arrow-left': ArrowLeft,
		briefcase: Briefcase,
		check: Check,
		'chevron-down': ChevronDown,
		church: Church,
		compass: Compass,
		'external-link': ExternalLink,
		globe: Globe,
		'graduation-cap': GraduationCap,
		'heart-pulse': HeartPulse,
		house: House,
		info: Info,
		languages: Languages,
		'message-square': MessageSquare,
		phone: Phone,
		printer: Printer,
		scale: Scale,
		search: Search,
		'share-2': Share2,
		'shield-check': ShieldCheck,
		siren: Siren,
		x: X
	};

	let { name, size = 22 }: { name: string; size?: number } = $props();
	const Component = $derived(ICONS[name as keyof typeof ICONS] ?? Info);
</script>

<Component {size} strokeWidth={2.25} aria-hidden="true" class="icon" />
