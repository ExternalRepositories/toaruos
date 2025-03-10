#include <stdint.h>
#include "options.h"
#include "text.h"
#include "util.h"
#include "kbd.h"

int boot_edit = 0;

int boot_editor(void) {
	int len    = strlen(cmdline);
	int cursor = len;

	while (1) {
		move_cursor(0,0);
		for (int i = 0; i <= len; ++i) {
			set_attr(i == cursor ? 0x70 : 0x07);
			print_((char[]){cmdline[i],'\0'});
		}
		print_(" ");
		set_attr(0x07);
		do {
			do {
				print_(" ");
			} while (x);
		} while (y);

		char data = 0;
		int status = read_key(&data);

		if (status == 0) {
			/* Handle a few special characters */
			if (data == '\n') {
				return 1;
			} else if (data == 27) {
				return 0;
			} else if (data == '\b') {
				if (!cursor) continue;
				if (cursor == len) {
					cmdline[len-1] = '\0';
					cursor--;
					len--;
				} else {
					cmdline[cursor-1] = '\0';
					strcat(cmdline,&cmdline[cursor]);
					cursor--;
					len--;
				}
			} else {
				if (len > 1022) continue;
				/* Move everything from the cursor onward forward */
				if (cursor < len) {
					int x = len + 1;
					while (x > cursor) {
						cmdline[x] = cmdline[x-1];
						x--;
					}
				}
				cmdline[cursor] = data;
				len++;
				cursor++;
			}
		} else if (status == 2) {
			/* Left */
			if (cursor) cursor--;
		} else if (status == 3) {
			/* Right */
			if (cursor < len) cursor++;
		} else if (status == 4) {
			/* Shift-left: Word left */
			while (cursor && cmdline[cursor] == ' ') cursor--;
			while (cursor && cmdline[cursor] != ' ') cursor--;
		} else if (status == 5) {
			/* Shift-right: Word right */
			while (cursor < len && cmdline[cursor] == ' ') cursor++;
			while (cursor < len && cmdline[cursor] != ' ') cursor++;
		}
	}
}

