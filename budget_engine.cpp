#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string>
#include <iomanip>
#include <algorithm>
#include <numeric>
#include <ctime>
#include <stdexcept>
enum class TransactionType { INCOME, EXPENSE };

struct Transaction {
    int         id;
    std::string date;       // year - month - day
    std::string category;
    std::string description;
    double      amount;
    TransactionType type;
};

struct BudgetSummary {
    double totalIncome;
    double totalExpenses;
    double netBalance;
    std::map<std::string, double> categoryTotals;
    std::map<std::string, double> monthlyTotals;
};

std::string escapeCSV(const std::string& s) {
    if (s.find(',') != std::string::npos || s.find('"') != std::string::npos) {
        std::string out = "\"";
        for (char c : s) { if (c == '"') out += '"'; out += c; }
        return out + '"';
    }
    return s;
}

std::vector<std::string> parseCSVLine(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    bool inQuotes = false;
    for (size_t i = 0; i < line.size(); ++i) {
        char c = line[i];
        if (c == '"') {
            if (inQuotes && i + 1 < line.size() && line[i + 1] == '"') { field += '"'; ++i; }
            else inQuotes = !inQuotes;
        } else if (c == ',' && !inQuotes) {
            fields.push_back(field); field.clear();
        } else {
            field += c;
        }
    }
    fields.push_back(field);
    return fields;
}

class BudgetTracker {
private:
    std::vector<Transaction> transactions;
    std::string dataFile;
    int nextId = 1;

    void recalcNextId() {
        for (auto& t : transactions)
            if (t.id >= nextId) nextId = t.id + 1;
    }

public:
    explicit BudgetTracker(const std::string& file = "transactions.csv")
        : dataFile(file) { load(); }

    void load() {
        transactions.clear();
        std::ifstream f(dataFile);
        if (!f.is_open()) return;

        std::string line;
        std::getline(f, line); // ??? wtf?

        while (std::getline(f, line)) {
            if (line.empty()) continue;
            auto fields = parseCSVLine(line);
            if (fields.size() < 6) continue;

            Transaction t;
            try {
                t.id          = std::stoi(fields[0]);
                t.date        = fields[1];
                t.category    = fields[2];
                t.description = fields[3];
                t.amount      = std::stod(fields[4]);
                t.type        = (fields[5] == "INCOME") ? TransactionType::INCOME
                                                        : TransactionType::EXPENSE;
                transactions.push_back(t);
            } catch (...) {}
        }
        recalcNextId();
    }

    void save() const {
        std::ofstream f(dataFile);
        f << "id,date,category,description,amount,type\n";
        for (auto& t : transactions) {
            f << t.id << ","
              << escapeCSV(t.date) << ","
              << escapeCSV(t.category) << ","
              << escapeCSV(t.description) << ","
              << std::fixed << std::setprecision(2) << t.amount << ","
              << (t.type == TransactionType::INCOME ? "INCOME" : "EXPENSE") << "\n";
        }
    }

    int addTransaction(const std::string& date, const std::string& category,
                       const std::string& desc, double amount, TransactionType type) {
        Transaction t { nextId++, date, category, desc, amount, type };
        transactions.push_back(t);
        save();
        return t.id;
    }

    bool deleteTransaction(int id) {
        auto it = std::remove_if(transactions.begin(), transactions.end(),
                                 [id](const Transaction& t){ return t.id == id; });
        if (it == transactions.end()) return false;
        transactions.erase(it, transactions.end());
        save();
        return true;
    }

    const std::vector<Transaction>& all() const { return transactions; }

    BudgetSummary summarize(const std::string& monthFilter = "") const {
        BudgetSummary s{};
        for (auto& t : transactions) {
            if (!monthFilter.empty() && t.date.substr(0, 7) != monthFilter) continue;
            if (t.type == TransactionType::INCOME) {
                s.totalIncome += t.amount;
            } else {
                s.totalExpenses += t.amount;
                s.categoryTotals[t.category] += t.amount;
            }
            s.monthlyTotals[t.date.substr(0, 7)] += (t.type == TransactionType::INCOME
                                                       ? t.amount : -t.amount);
        }
        s.netBalance = s.totalIncome - s.totalExpenses;
        return s;
    }
};

void printHeader() {
    std::cout << "\n╔══════════════════════════════════════════╗\n"
              << "║          BUDGET TRACKER            ║\n"
              << "║               :3                   ║\n"
              << "╚══════════════════════════════════════════╝\n\n";
}

void printMenu() {
    std::cout << "  [1] Add Income\n"
              << "  [2] Add Expense\n"
              << "  [3] List All Transactions\n"
              << "  [4] Show Summary\n"
              << "  [5] Monthly Report\n"
              << "  [6] Delete Transaction\n"
              << "  [0] Exit\n"
              << "\n  Choice: ";
}

std::string currentDate() {
    time_t now = time(nullptr);
    char buf[11];
    strftime(buf, sizeof(buf), "%Y-%m-%d", localtime(&now));
    return buf;
}

void listTransactions(const BudgetTracker& bt) {
    auto& txns = bt.all();
    if (txns.empty()) { std::cout << "  No transactions found.\n"; return; }

    std::cout << "\n  " << std::left
              << std::setw(5)  << "ID"
              << std::setw(12) << "Date"
              << std::setw(16) << "Category"
              << std::setw(22) << "Description"
              << std::setw(12) << "Amount"
              << "Type\n";
    std::cout << "  " << std::string(75, '-') << "\n";

    for (auto& t : txns) {
        std::string amtStr = "$" + std::to_string((int)t.amount) + "."
                           + std::to_string((int)(t.amount * 100) % 100);
        std::cout << "  " << std::left
                  << std::setw(5)  << t.id
                  << std::setw(12) << t.date
                  << std::setw(16) << t.category
                  << std::setw(22) << t.description.substr(0, 20)
                  << std::setw(12) << std::fixed << std::setprecision(2) << t.amount
                  << (t.type == TransactionType::INCOME ? "INCOME" : "EXPENSE") << "\n";
    }
    std::cout << "\n";
}

void showSummary(const BudgetTracker& bt, const std::string& month = "") {
    auto s = bt.summarize(month);
    std::cout << "\n  Budget Summary"
              << (month.empty() ? " (All Time)" : " (" + month + ")") << " ──\n";
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "  Total Income:   $" << s.totalIncome   << "\n"
              << "  Total Expenses: $" << s.totalExpenses << "\n"
              << "  Net Balance:    $" << s.netBalance    << "\n\n";

    if (!s.categoryTotals.empty()) {
        std::cout << "  Expenses by Category:\n";
        for (auto& [cat, amt] : s.categoryTotals)
            std::cout << "    • " << std::left << std::setw(18) << cat << " $" << amt << "\n";
    }
    std::cout << "\n";
}

int main() {
    printHeader();
    BudgetTracker bt("transactions.csv");

    int choice;
    while (true) {
        printMenu();
        std::cin >> choice;
        std::cin.ignore();

        if (choice == 0) {
            std::cout << "\n  Data saved to transactions.csv\n\n";
            break;
        }

        if (choice == 1 || choice == 2) {
            TransactionType type = (choice == 1) ? TransactionType::INCOME : TransactionType::EXPENSE;
            std::string label = (type == TransactionType::INCOME) ? "Income" : "Expense";

            std::string date, cat, desc;
            double amount;

            std::cout << "  Date [" << currentDate() << "]: ";
            std::getline(std::cin, date);
            if (date.empty()) date = currentDate();

            std::cout << "  Category: ";
            std::getline(std::cin, cat);

            std::cout << "  Description: ";
            std::getline(std::cin, desc);

            std::cout << "  Amount: $";
            std::cin >> amount;
            std::cin.ignore();

            int id = bt.addTransaction(date, cat, desc, amount, type);
            std::cout<<label << " added (ID: " << id << ")\n\n";

        } else if (choice == 3) {
            listTransactions(bt);

        } else if (choice == 4) {
            showSummary(bt);

        } else if (choice == 5) {
            std::string month;
            std::cout << "  Month (YYYY-MM): ";
            std::getline(std::cin, month);
            showSummary(bt, month);

        } else if (choice == 6) {
            int id;
            std::cout << "  Transaction ID to delete: ";
            std::cin >> id;
            std::cin.ignore();
            if (bt.deleteTransaction(id))
                std::cout << " Transaction " << id << " deleted.\n\n";
            else
                std::cout << " ID not found\n\n";
        }
    }
    return 0;
}
