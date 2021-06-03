function openTab(evt, tabName) {
// Declare all variables
	var i, tabcontent, tab_links, element;

// Get all elements with class="open" and hide them
	tabcontent = document.getElementsByClassName("tabcontent open");
	for (i = 0; i < tabcontent.length; i++) {
		tabcontent[i].className = "tabcontent closed";
	}

// Get all elements with class="tab_links" and remove the class "active"
	tab_links = document.getElementsByClassName("tab_links");
	for (i = 0; i < tab_links.length; i++) {
		tab_links[i].className = tab_links[i].className.replace(" active", "");
	}

// Show the current tab, and add an "active" class to the button that opened the tab
	element = document.getElementById(tabName)
	element.className = "tabcontent open";
	evt.currentTarget.className += " active";
}

// Get the element with id="defaultOpen" and click on it
function loaded() {
	document.getElementById("defaultClosed").click();
	document.getElementById("defaultOpen").click();
};
