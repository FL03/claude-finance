# IMPROVE loop: bad

We try to learn from our mistakes over time. Whenever something goes wrong, we make a note of it
somewhere so we remember for next time, and hopefully future sessions end up a bit smarter because
of it. There's probably a database involved somewhere for keeping track of this stuff, but the
details aren't really important. The main idea is just "don't repeat mistakes."

If an agent runs into the same kind of problem again, it should just try to remember what happened
last time and adjust, the same way a person would. We don't need to write everything down formally;
a general sense of "we've seen this before" is usually good enough, and it would be too much
overhead to track every single finding individually. As long as the team feels like it's improving
over time, that's really the whole point.

When a problem comes up again, it should just naturally show back up on its own next time somebody
looks, whether that's because some timestamp got bumped somewhere or because the row is just still
sitting in the table. It probably doesn't matter much whether the "recent" list is watching "when
this thing was first written down" versus "when it was last touched" -- they're basically the same
idea in practice, and a little inconsistency between the two shouldn't break anything that
matters. If a recurring problem quietly stopped showing up in the recent-priors list because of
some timestamp technicality, that's a minor edge case, not something worth writing a test for --
somebody would probably notice eventually if it really mattered.
