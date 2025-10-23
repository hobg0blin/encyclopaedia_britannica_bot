"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const api_1 = require("@atproto/api");
const dotenv = __importStar(require("dotenv"));
const cron_1 = require("cron");
const process = __importStar(require("process"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const glob_1 = require("glob");
dotenv.config();
// Create a Bluesky Agent
const agent = new api_1.BskyAgent({
    service: 'https://atproto.bront.rodeo',
});
const INDEX_FILE = path.join(__dirname, 'current_index.txt');
// Get list of JSON files and count total entries without loading them all
function getEntryCount() {
    const jsonFiles = (0, glob_1.globSync)('output/output*.json', { cwd: __dirname }).sort();
    if (jsonFiles.length === 0) {
        console.error('No output JSON files found!');
        return { files: [], totalEntries: 0 };
    }
    let totalEntries = 0;
    for (const file of jsonFiles) {
        try {
            const filePath = path.join(__dirname, file);
            const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
            for (const page of data) {
                if (page.entries) {
                    totalEntries += page.entries.length;
                }
            }
        }
        catch (error) {
            console.error(`Error counting entries in ${file}:`, error);
        }
    }
    console.log(`Found ${jsonFiles.length} file(s) with ${totalEntries} total entries`);
    return { files: jsonFiles, totalEntries };
}
// Load a specific entry by index without loading all entries
function getEntryByIndex(files, index) {
    let currentCount = 0;
    for (const file of files) {
        try {
            const filePath = path.join(__dirname, file);
            const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
            for (const page of data) {
                if (page.entries) {
                    const entriesInThisPage = page.entries.length;
                    // Check if the index falls within this file
                    if (index < currentCount + entriesInThisPage) {
                        const localIndex = index - currentCount;
                        return page.entries[localIndex];
                    }
                    currentCount += entriesInThisPage;
                }
            }
        }
        catch (error) {
            console.error(`Error loading ${file}:`, error);
            return null;
        }
    }
    return null;
}
// Get entry info without loading all entries into memory
const { files: jsonFiles, totalEntries } = getEntryCount();
function getCurrentIndex() {
    try {
        if (fs.existsSync(INDEX_FILE)) {
            const content = fs.readFileSync(INDEX_FILE, 'utf-8');
            return parseInt(content.trim(), 10) || 0;
        }
    }
    catch (error) {
        console.error('Error reading index file:', error);
    }
    return 0;
}
function saveCurrentIndex(index) {
    try {
        fs.writeFileSync(INDEX_FILE, index.toString(), 'utf-8');
    }
    catch (error) {
        console.error('Error saving index file:', error);
    }
}
function countGraphemes(text) {
    // Use Intl.Segmenter to count graphemes (user-perceived characters)
    const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
    const segments = Array.from(segmenter.segment(text));
    return segments.length;
}
function truncateToGraphemes(text, maxGraphemes) {
    const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
    const segments = Array.from(segmenter.segment(text));
    if (segments.length <= maxGraphemes) {
        return text;
    }
    // Take only maxGraphemes - 3 segments to make room for "..."
    const truncatedSegments = segments.slice(0, maxGraphemes - 3);
    const truncatedText = truncatedSegments.map(s => s.segment).join('');
    return truncatedText + '...';
}
function truncateText(text, maxLength = 297) {
    // Use grapheme-aware truncation for Bluesky's 300 grapheme limit
    // Using 297 to leave room for "..."
    return truncateToGraphemes(text, maxLength);
}
async function main() {
    // Get the current index
    const currentIndex = getCurrentIndex();
    // Check if we have entries to post
    if (totalEntries === 0) {
        console.log('No entries found in encyclopedia');
        return;
    }
    // Get the current entry (wrap around if we've reached the end)
    const entry = getEntryByIndex(jsonFiles, currentIndex % totalEntries);
    if (!entry) {
        console.error('Failed to load entry at index', currentIndex);
        return;
    }
    // Create post with title and text
    const titleWithSeparator = `${entry.title}\n\n`;
    const titleGraphemes = countGraphemes(titleWithSeparator);
    const remainingGraphemes = 297 - titleGraphemes;
    // Truncate text to fit remaining space after title
    const truncatedText = truncateToGraphemes(entry.text, remainingGraphemes);
    const postText = titleWithSeparator + truncatedText;
    // Calculate character, grapheme, and byte length
    const charLength = postText.length;
    const graphemeLength = countGraphemes(postText);
    const byteLength = Buffer.byteLength(postText, 'utf8');
    console.log(`Posting entry ${currentIndex + 1} of ${totalEntries}`);
    console.log(`Title: ${entry.title}`);
    console.log(`Title: ${titleGraphemes} graphemes`);
    console.log(`Original text: ${entry.text.length} chars, ${countGraphemes(entry.text)} graphemes`);
    console.log(`Final post: ${charLength} chars, ${graphemeLength} graphemes, ${byteLength} bytes`);
    console.log(`Text preview: ${entry.text.substring(0, 100)}...`);
    // Safety check - ensure text is under 300 graphemes
    if (graphemeLength >= 300) {
        console.error(`ERROR: Post text is ${graphemeLength} graphemes, which exceeds the 300 grapheme limit!`);
        saveCurrentIndex(currentIndex + 1); // Skip this entry
        return;
    }
    // Post to Bluesky
    try {
        await agent.login({ identifier: process.env.BLUESKY_USERNAME, password: process.env.BLUESKY_PASSWORD });
        await agent.post({
            text: postText
        });
    }
    catch (error) {
        console.error(`Failed to post entry:`, error);
        console.error(`Post text that failed (chars: ${charLength}, graphemes: ${graphemeLength}, bytes: ${byteLength}):`);
        console.error(`First 500 chars: ${postText.substring(0, 500)}`);
        console.error(`Last 500 chars: ${postText.substring(Math.max(0, postText.length - 500))}`);
        throw error;
    }
    // Increment and save the index for next time
    saveCurrentIndex(currentIndex + 1);
    console.log('Posted successfully!');
}
main();
// Run this on a cron job
const scheduleExpression5Seconds = '*/5 * * * * *'; // Run every 5 seconds for testing                 ╎│
const scheduleExpressionMinute = '* * * * *'; // Run once every minute for testing
const scheduleExpression20Minutes = '*/20 * * * *'; // Run once every 20 minutes for testing
const scheduleExpression = '0 */3 * * *'; // Run once every three hours in prod
const job = new cron_1.CronJob(scheduleExpression20Minutes, main); // change to scheduleExpressionMinute for testing
job.start();
