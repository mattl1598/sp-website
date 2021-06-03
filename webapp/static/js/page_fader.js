function fadePage() {
	if (!window.AnimationEvent) { return; }
	let fader = document.getElementById('content');
    fader.classList.toggle('fade-out');
}