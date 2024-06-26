# Orca
#
# Copyright 2004-2008 Sun Microsystems Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., Franklin Street, Fifth Floor,
# Boston MA  02110-1301 USA.

"""Custom script for gedit."""

__id__        = "$Id$"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005-2008 Sun Microsystems Inc."
__license__   = "LGPL"

import orca.focus_manager as focus_manager
import orca.scripts.toolkits.gtk as gtk
from orca.ax_object import AXObject
from orca.ax_utilities import AXUtilities
from .spellcheck import SpellCheck


class Script(gtk.Script):

    def __init__(self, app):
        """Creates a new script for the given application."""

        gtk.Script.__init__(self, app)

    def getSpellCheck(self):
        """Returns the spellcheck for this script."""

        return SpellCheck(self)

    def getAppPreferencesGUI(self):
        """Returns a GtkGrid containing the application unique configuration
        GUI items for the current application."""

        from gi.repository import Gtk

        grid = Gtk.Grid()
        grid.set_border_width(12)
        grid.attach(self.spellcheck.getAppPreferencesGUI(), 0, 0, 1, 1)
        grid.show_all()

        return grid

    def getPreferencesFromGUI(self):
        """Returns a dictionary with the app-specific preferences."""

        return self.spellcheck.getPreferencesFromGUI()

    def locusOfFocusChanged(self, event, oldFocus, newFocus):
        """Handles changes of focus of interest to the script."""

        if self.spellcheck.isSuggestionsItem(newFocus):
            includeLabel = not self.spellcheck.isSuggestionsItem(oldFocus)
            self.updateBraille(newFocus)
            self.spellcheck.presentSuggestionListItem(includeLabel=includeLabel)
            return

        super().locusOfFocusChanged(event, oldFocus, newFocus)

    def onActiveDescendantChanged(self, event):
        """Callback for object:active-descendant-changed accessibility events."""

        if event.source == self.spellcheck.getSuggestionsList():
            return

        gtk.Script.onActiveDescendantChanged(self, event)

    def onCaretMoved(self, event):
        """Callback for object:text-caret-moved accessibility events."""

        if AXUtilities.is_multi_line(event.source):
            self.spellcheck.setDocumentPosition(event.source, event.detail1)

        gtk.Script.onCaretMoved(self, event)

    def onFocusedChanged(self, event):
        """Callback for object:state-changed:focused accessibility events."""

        if not event.detail1:
            return

        gtk.Script.onFocusedChanged(self, event)

    def onNameChanged(self, event):
        """Callback for object:property-change:accessible-name events."""

        if not self.spellcheck.isActive():
            gtk.Script.onNameChanged(self, event)
            return

        name = AXObject.get_name(event.source)
        if name == self.spellcheck.getMisspelledWord():
            self.spellcheck.presentErrorDetails()
            return

        parent = AXObject.get_parent(event.source)
        if parent != self.spellcheck.getSuggestionsList() \
           or not AXUtilities.is_focused(parent):
            return

        entry = self.spellcheck.getChangeToEntry()
        if name != self.utilities.displayedText(entry):
            return

        # If we're here, the locusOfFocus was in the selection list when
        # that list got destroyed and repopulated. Focus is still there.
        focus_manager.getManager().set_locus_of_focus(event, event.source, False)
        self.updateBraille(event.source)

    def onSensitiveChanged(self, event):
        """Callback for object:state-changed:sensitive accessibility events."""

        if event.source == self.spellcheck.getChangeToEntry() \
           and self.spellcheck.presentCompletionMessage():
            return

        gtk.Script.onSensitiveChanged(self, event)

    def onTextSelectionChanged(self, event):
        """Callback for object:text-selection-changed accessibility events."""

        focus = focus_manager.getManager().get_locus_of_focus()
        if event.source == focus:
            gtk.Script.onTextSelectionChanged(self, event)
            return

        if not self.utilities.isSearchEntry(focus, True):
            return

        if not (AXUtilities.is_showing(event.source) and AXUtilities.is_visible(event.source)):
            return

        # To avoid extreme chattiness.
        keyString, mods = self.utilities.lastKeyAndModifiers()
        if keyString in ["BackSpace", "Delete"]:
            return

        self.sayLine(event.source)

    def onWindowActivated(self, event):
        """Callback for window:activate accessibility events."""

        gtk.Script.onWindowActivated(self, event)
        if not self.spellcheck.isCheckWindow(event.source):
            return

        self.spellcheck.presentErrorDetails()
        entry = self.spellcheck.getChangeToEntry()
        focus_manager.getManager().set_locus_of_focus(None, entry, False)
        self.updateBraille(entry)

    def onWindowDeactivated(self, event):
        """Callback for window:deactivate accessibility events."""

        gtk.Script.onWindowDeactivated(self, event)
        self.spellcheck.deactivate()
